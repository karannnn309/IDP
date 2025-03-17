import fitz  # PyMuPDF for PDF processing
import pytesseract
from PIL import Image
import requests
import matplotlib.pyplot as plt
import seaborn as sns
from fuzzywuzzy import fuzz
import docx  # python-docx for .docx processing
from pdf2image import convert_from_path  # Convert PDF to images (for OCR)
import mimetypes
import google.generativeai as genai
import pandas as pd
import matplotlib
from pdfminer.high_level import extract_text
import cv2
import json
import os
from django.conf import settings
from difflib import SequenceMatcher
import re



# Set the Tesseract OCR path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'



GEMINI_API_KEY = "AIzaSyASdSsKECLMv-my69VBSF5ZgyMrCcCy9rg"  # Replace with your actual API key
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
matplotlib.use('Agg')




def extract_text_from_pdf(file_path):
    text = ""

    # First, try extracting using PyMuPDF
    try:
        pdf_document = fitz.open(file_path)
        for page in pdf_document:
            text += page.get_text("text") + "\n"
        if text.strip():
            return text  # Return if successful
    except Exception as e:
        print(f"Error using PyMuPDF: {e}")

    # If PyMuPDF fails, try PDFMiner
    try:
        text = extract_text(file_path)
        return text if text.strip() else "No text extracted."
    except Exception as e:
        print(f"Error using PDFMiner: {e}")

    return "Text extraction failed."





def extract_text_from_scanned_pdf(file_path):
    images = convert_from_path(file_path, dpi=300)  # Convert PDF to images
    text = ""

    for image in images:
        text += pytesseract.image_to_string(image, lang="eng") + "\n"

    return text if text.strip() else "No text extracted."


def extract_text_from_docx(file_path):
    doc = docx.Document(file_path)
    text = ""

    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"  # Preserve formatting

    return text if text.strip() else "No text extracted."

def preprocess_and_extract_text(image_path):
    image = cv2.imread(image_path)
    
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply thresholding to remove noise
    processed = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                      cv2.THRESH_BINARY, 31, 2)

    # Save and read with OCR
    cv2.imwrite("processed_image.png", processed)
    text = pytesseract.image_to_string(Image.open("processed_image.png"), lang="eng")

    return text if text.strip() else "No text extracted."





def extract_text(file_path):
    """Universal function to extract text from PDFs, scanned PDFs, DOCX, and images."""
    mime_type = mimetypes.guess_type(file_path)[0]
    extracted_text = ""

    try:
        # 1️⃣ **For PDFs**
        if file_path.endswith(".pdf") or mime_type == "application/pdf":
            extracted_text = extract_text_from_pdf(file_path)

            # If the extracted text is empty, try OCR (for scanned PDFs)
            if not extracted_text.strip():
                extracted_text = extract_text_from_scanned_pdf(file_path)

        # 2️⃣ **For DOCX**
        elif file_path.endswith(".docx") or mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            extracted_text = extract_text_from_docx(file_path)

        # 3️⃣ **For Images**
        elif file_path.lower().endswith((".png", ".jpg", ".jpeg")) or mime_type.startswith("image/"):
            extracted_text = preprocess_and_extract_text(file_path)
        
        else:
            print(f"⚠️ Unsupported file type: {file_path}")
            return None

    except Exception as e:
        print(f"❌ Error extracting text from {file_path}: {e}")
    
    
    
    return extracted_text.strip()




# Function to process extracted text using Gemini API
  # Replace with actual endpoint

def send_to_gemini(extracted_text, expected_data):
    """Send extracted text & expected data to Gemini API and return a structured JSON response."""
    try:
        print("🔄 Sending extracted text & expected data to Gemini API...")

        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": f"""
                            You are an AI that extracts structured data from text.
                            Here is a document's extracted raw text. I expect the output in JSON format matching the expected structure.

                            - **Strictly return only JSON**. No explanations, no extra text, just JSON.
                            - Ensure valid JSON syntax.
                            - Do not add extra keys or modify expected structure.
                            - If a value is missing, return `null`.

                            Extracted Data:
                            {extracted_text}

                            Expected Data Format:
                            {json.dumps(expected_data, indent=2)}

                            Output JSON:
                            """
                        }
                    ]
                }
            ]
        }

        headers = {"Content-Type": "application/json"}
        response = requests.post(GEMINI_API_URL, headers=headers, json=payload)

        if response.status_code != 200:
            print(f"❌ API Error: {response.status_code} - {response.text}")
            return {"error": f"API Error: {response.status_code}"}

        response_json = response.json()

        # Extract the actual response text from Gemini
        if "candidates" in response_json and len(response_json["candidates"]) > 0:
            gemini_text = response_json["candidates"][0]["content"]["parts"][0]["text"]
            
            try:
                # Direct JSON parsing attempt
                structured_response = json.loads(gemini_text)
                print("structured_response")
                return structured_response
            except json.JSONDecodeError:
                print("⚠️ Raw response is not valid JSON. Attempting extraction...")

                # Extract JSON content from raw response using regex
                json_match = re.search(r'\{.*\}', gemini_text, re.DOTALL)
                if json_match:
                    try:
                        extracted_json = json.loads(json_match.group(0))
                        print("extracted_json:",extracted_json)
                        return extracted_json
                    except json.JSONDecodeError:
                        print("❌ Extracted content is still not valid JSON.")

                return {"error": "Invalid JSON response", "raw_response": gemini_text}

        return {"error": "No valid response from Gemini API"}

    except requests.exceptions.RequestException as e:
        print(f"❌ Request Exception: {e}")
        return {"error": str(e)}
    



def calculate_mismatch_percentage(expected, extracted):
    """Calculate mismatch percentage between expected and extracted values."""
    if not expected or not extracted:
        return 100.0  # Full mismatch if one of them is missing
    similarity = SequenceMatcher(None, str(expected), str(extracted)).ratio()
    return round((1 - similarity) * 100, 2)  # Convert to percentage

def validate_gemini_response(expected_data, gemini_response):
    """Compares expected data with Gemini's response and returns mismatches & similarities."""
    
    mismatches = {}
    similarities = {}
    missing_fields = []
    extra_fields = []

    # Check for missing fields in Gemini's response
    for key, expected_value in expected_data.items():
        if key not in gemini_response:
            missing_fields.append(key)
        else:
            extracted_value = gemini_response[key]
            mismatch_percentage = calculate_mismatch_percentage(expected_value, extracted_value)
            
            if mismatch_percentage == 0:
                similarities[key] = extracted_value  # ✅ Exact match
            else:
                mismatches[key] = {
                    "Expected": expected_value,
                    "Extracted": extracted_value,
                    "Mismatch %": mismatch_percentage  # ❌ Store mismatch percentage
                }

    # Check for extra fields present in Gemini response but not expected
    for key in gemini_response.keys():
        if key not in expected_data:
            extra_fields.append(key)

    # Structure the final validation report
    validation_result = {
        "mismatches": mismatches,
        "similarities": similarities,
        "missing_fields": missing_fields,
        "extra_fields": extra_fields
    }

    return validation_result



# ✅ Mismatch Visualization Function
def visualize_mismatches(validation_result, applicant_id):
    """
    Generate a mismatch visualization chart based on validation results.
    """
    if not isinstance(validation_result, dict) or not validation_result.get("mismatches"):
        print("✅ No mismatches found, skipping visualization.")
        return None

    mismatches = validation_result["mismatches"]
    mismatch_data = []
    
    try:
        # Extract mismatch data
        for field, values in mismatches.items():
            mismatch_data.append({
                "Field": field,
                "Expected": str(values.get("expected", "N/A")),
                "Extracted": str(values.get("actual", "N/A")),
                "Similarity": 0  # Placeholder for future similarity calculations
            })

        # Ensure we have data to visualize
        if not mismatch_data:
            print("✅ No valid mismatch data to visualize.")
            return None

        # Create DataFrame for visualization
        df = pd.DataFrame(mismatch_data)
        
        if df.empty:
            print("✅ DataFrame is empty, skipping visualization.")
            return None

        # Plot mismatches
        plt.figure(figsize=(12, 6))
        sns.barplot(x="Field", y=[1]*len(df), hue="Field", data=df, palette="coolwarm", legend=False)
        plt.xticks(rotation=45, ha='right')
        plt.xlabel("Field Name")
        plt.ylabel("Mismatch Indicator")
        plt.title("Mismatches in Application")
        plt.axhline(1, color="r", linestyle="dashed", label="Mismatch Present")
        plt.legend()

        # Ensure MEDIA_ROOT exists
        media_path = settings.MEDIA_ROOT if hasattr(settings, "MEDIA_ROOT") else "media"
        os.makedirs(media_path, exist_ok=True)

        # Save plot in MEDIA folder
        mismatch_plot_path = os.path.join(media_path, f"mismatch_plot_{applicant_id}.png")
        plt.savefig(mismatch_plot_path, bbox_inches="tight")
        plt.close()

        return mismatch_plot_path

    except Exception as e:
        print(f"❌ Error in visualize_mismatches: {e}")
        return None