from django.shortcuts import render, redirect,get_object_or_404
from django.conf import settings
from .forms import ApplicantForm, DocumentForm
from .models import Applicant, Document
import os
import json
from .utils import *




# View to handle document submission and analysis
def submit_application(request):
    if request.method == "POST":
        applicant_form = ApplicantForm(request.POST)
        document_form = DocumentForm(request.POST, request.FILES)

        if applicant_form.is_valid() and document_form.is_valid():
            applicant = applicant_form.save()
            extracted_text = ""

            # Extract text from uploaded documents
            for file in request.FILES.getlist("file"):
                document = Document.objects.create(applicant=applicant, file=file)
                document_path = document.file.path

                if not os.path.exists(document_path):
                    print(f"❌ File not found: {document_path}")
                    continue

                print(f"📂 Processing file: {document_path}")
                try:
                    text = extract_text(document_path)
                    if text.strip():
                        document.extracted_text = text
                        document.save()
                        extracted_text += text + "\n"
                    else:
                        print("⚠️ No text extracted from file.")
                except Exception as e:
                    print(f"❌ Error extracting text: {e}")

            # Process with Gemini if extraction is successful
            if extracted_text.strip():
                expected_data = {
                    str(key): (request.POST.getlist(key) if len(request.POST.getlist(key)) > 1 else request.POST.get(key))
                    for key in request.POST 
                    if key not in ["csrfmiddlewaretoken"] and key not in request.FILES
                }

                # Send text to Gemini API and process the response
                gemini_response = send_to_gemini(extracted_text, expected_data)

                if gemini_response and "error" not in gemini_response:
                    try:
                        extracted_fields = {str(k): v for k, v in gemini_response.items()}  # Ensure JSON serializability
                        applicant.extracted_data = json.dumps(extracted_fields, indent=2)
                        applicant.expected_json = json.dumps(expected_data, indent=2)
                        applicant.save()

                        print(f"✅ Extracted Fields: {json.dumps(extracted_fields, indent=2)}")

                        # Validate extracted fields against expected data
                        validation_result = validate_gemini_response(expected_data, extracted_fields)
                        # 🔹 Calculate overall mismatch percentage
                        total_mismatches = sum(
                            mismatch["Mismatch %"] for mismatch in validation_result["mismatches"].values()
                        )
                        num_fields = len(expected_data)
                        
                        overall_mismatch_percentage = round(total_mismatches / num_fields, 2) if num_fields else 0
                        applicant.mismatches = json.dumps(validation_result, indent=2)
                        applicant.mismatch_percentage = overall_mismatch_percentage  # Save overall mismatch %
                        applicant.save()

                        print(f"🔍 Validation Result: {json.dumps(validation_result, indent=2)}")

                        # Generate mismatch visualization if mismatches exist
                        if validation_result.get("mismatches") or validation_result.get("missing_fields"):
                            visualize_mismatches(validation_result, applicant.id)

                    except Exception as e:
                        print(f"❌ Error processing Gemini response: {e}")

            return redirect("results", applicant_id=applicant.id)

    else:
        applicant_form = ApplicantForm()
        document_form = DocumentForm()

    return render(request, "submit_application.html", {"applicant_form": applicant_form, "document_form": document_form})

def applicant_results(request, applicant_id):
    applicant = get_object_or_404(Applicant, id=applicant_id)
    documents = Document.objects.filter(applicant=applicant)

    extracted_data = json.loads(applicant.extracted_data) if applicant.extracted_data else {}
    expected_data = json.loads(applicant.expected_json) if applicant.expected_json else {}
    mismatches = json.loads(applicant.mismatches) if applicant.mismatches else {}

    # Convert mismatches dictionary into a list for easy iteration in the template
    formatted_mismatches = []
    for field, details in mismatches.get("mismatches", {}).items():
        formatted_mismatches.append({
            "field": field,
            "expected": details.get("Expected", ""),
            "extracted": details.get("Extracted", ""),
            "mismatch_percentage": details.get("Mismatch %", 0),
        })

    # Generate mismatch visualization only if mismatches exist
    mismatch_plot_url = None
    if mismatches:
        mismatch_plot_path = visualize_mismatches(mismatches, applicant.id)
        if mismatch_plot_path:
            mismatch_plot_url = settings.MEDIA_URL + os.path.basename(mismatch_plot_path)

    return render(request, "results.html", {
        "applicant": applicant,
        "documents": documents,
        "extracted_data": extracted_data,
        "expected_data": expected_data,
        "mismatches": formatted_mismatches,  # ✅ Pass the processed list
        "mismatch_plot_path": mismatch_plot_url
    })
