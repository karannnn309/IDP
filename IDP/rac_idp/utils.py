import os
import json
import re
import mimetypes
import torch
import pytesseract
import docx
import requests
import fitz  # PyMuPDF
import cv2
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from PIL import Image
from pdf2image import convert_from_path
from difflib import SequenceMatcher
from django.conf import settings
from transformers import AutoProcessor, AutoModelForTokenClassification
import transformers
transformers.logging.set_verbosity_error()

# Load LayoutLM model and processor
MODEL_NAME = "microsoft/layoutlmv3-base"
processor = AutoProcessor.from_pretrained(MODEL_NAME, apply_ocr=False)  # Disable internal OCR
model = AutoModelForTokenClassification.from_pretrained(MODEL_NAME)

# Set up Tesseract OCR path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Set up Gemini API
GEMINI_API_KEY = "AIzaSyASdSsKECLMv-my69VBSF5ZgyMrCcCy9rg"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
matplotlib.use('Agg')

# 1️⃣ Detect File Type
def detect_file_type(file_path):
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type:
        if mime_type.startswith("image/"):
            return "image"
        elif mime_type == "application/pdf":
            return "pdf"
        elif mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return "docx"
    return "unsupported"

# 2️⃣ Extract Text from PDFs
def extract_text_from_pdf(file_path):
    text = ""
    try:
        pdf_document = fitz.open(file_path)
        for page in pdf_document:
            text += page.get_text("text") + "\n"
        if text.strip():
            return text
    except Exception as e:
        print(f"Error using PyMuPDF: {e}")
    return "Text extraction failed."

# 3️⃣ Convert PDFs to Images for LayoutLM Processing
def process_pdf(file_path):
    images = convert_from_path(file_path, dpi=300)
    return images

# 4️⃣ Load and Process Image Files
def preprocess_and_extract_text(image_path):
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    processed = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 2)

    # Save processed image
    cv2.imwrite("processed_image.png", processed)
    image = Image.open("processed_image.png")

    # Convert to RGB (3 channels) to avoid dimension issues
    image = image.convert("RGB")
    return image

# 5️⃣ Extract Text & Bounding Boxes using OCR
def extract_text_with_bboxes(image):
    ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    words, boxes = [], []

    # Get image dimensions
    img_width, img_height = image.size

    for i in range(len(ocr_data["text"])):
        if ocr_data["text"][i].strip():
            words.append(ocr_data["text"][i])
            x, y, w, h = ocr_data["left"][i], ocr_data["top"][i], ocr_data["width"][i], ocr_data["height"][i]

            # Normalize bounding boxes to [0, 1000]
            x_scaled = (x / img_width) * 1000
            y_scaled = (y / img_height) * 1000
            w_scaled = (w / img_width) * 1000
            h_scaled = (h / img_height) * 1000

            # Append normalized bounding box
            boxes.append([x_scaled, y_scaled, x_scaled + w_scaled, y_scaled + h_scaled])

    return words, boxes

# 6️⃣ Process with LayoutLM
def process_with_layoutlm(image):
    words, boxes = extract_text_with_bboxes(image)

    # Ensure boxes are of type torch.long (LongTensor)
    boxes = torch.tensor(boxes, dtype=torch.long)  # Cast boxes to LongTensor

    # Now pass the OCR results to LayoutLM (without applying internal OCR)
    encoded_inputs = processor(images=image, text=words, boxes=boxes, return_tensors="pt", truncation=True, padding=True)

    with torch.no_grad():
        outputs = model(**encoded_inputs)

    logits = outputs.logits
    predictions = torch.argmax(logits, dim=-1)

    extracted_text = " ".join(words)
    return extracted_text

# 7️⃣ Extract Text from DOCX
def extract_text_from_docx(file_path):
    doc = docx.Document(file_path)
    text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
    return text if text.strip() else "No text extracted."

# 8️⃣ Main Function to Process Any Document Type
def extract_text(file_path):
    file_type = detect_file_type(file_path)

    if file_type == "pdf":
        images = process_pdf(file_path)
        extracted_texts = [process_with_layoutlm(image) for image in images]
        return "\n".join(extracted_texts)

    elif file_type == "image":
        image = preprocess_and_extract_text(file_path)
        return process_with_layoutlm(image)

    elif file_type == "docx":
        return extract_text_from_docx(file_path)

    else:
        print("Unsupported file type.")
        return None


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
                            Here is a document's extracted raw text. Your goal is to extract values based on the expected structure. 

                            **Guidelines:**
                            - If a field name is missing in the extracted text, infer it using its value.
                            - If a value is missing, return `null`.
                            - **Ensure valid JSON syntax. Return only JSON, no explanations.**
                            - Do not add extra keys or modify the expected structure.
                            - If a value appears but is not labeled, match it to the closest expected field using semantic similarity.

                            **Extracted Data:**
                            {extracted_text}

                            **Expected Data Format:**
                            {json.dumps(expected_data, indent=2)}

                            **Output JSON:**
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
                return structured_response
            except json.JSONDecodeError:
                print("⚠️ Raw response is not valid JSON. Attempting extraction...")

                # Extract JSON content from raw response using regex
                json_match = re.search(r'\{.*\}', gemini_text, re.DOTALL)
                if json_match:
                    try:
                        extracted_json = json.loads(json_match.group(0))
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

            # Convert both to lowercase for case-insensitive comparison
            if isinstance(expected_value, str) and isinstance(extracted_value, str):
                expected_value_lower = expected_value.lower().strip()
                extracted_value_lower = extracted_value.lower().strip()
            else:
                expected_value_lower = expected_value
                extracted_value_lower = extracted_value

            mismatch_percentage = calculate_mismatch_percentage(expected_value_lower, extracted_value_lower)

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
                "Expected": str(values.get("Expected", "N/A")),  # Correct keys
                "Extracted": str(values.get("Extracted", "N/A")),
                "Mismatch Percentage": values.get("Mismatch %", 0)  # Extract mismatch percentage
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

        # Plot mismatches with correct percentages
        plt.figure(figsize=(12, 6))
        sns.barplot(x="Field", y="Mismatch Percentage", hue="Field", data=df, palette="coolwarm", legend=False)

        plt.xticks(rotation=45, ha='right')
        plt.xlabel("Field Name")
        plt.ylabel("Mismatch Percentage (%)")
        plt.title("Mismatches in Application")

        # Save plot in MEDIA folder
        media_path = settings.MEDIA_ROOT if hasattr(settings, "MEDIA_ROOT") else "media"
        os.makedirs(media_path, exist_ok=True)

        mismatch_plot_path = os.path.join(media_path, f"mismatch_plot_{applicant_id}.png")
        plt.savefig(mismatch_plot_path, bbox_inches="tight")
        plt.close()

        return mismatch_plot_path

    except Exception as e:
        print(f"❌ Error in visualize_mismatches: {e}")
        return None

