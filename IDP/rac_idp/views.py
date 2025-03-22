from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from .forms import *
from .models import *
import os
import json
from .utils import *
import requests
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required


def landing_page(request):
    return render(request, "landing.html")

def signup_view(request):
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            # Create an Applicant record for the user
            Applicant.objects.create(user=user)  # Automatically create the applicant on signup
            return redirect('/login/')  # Redirect to a page after successful signup
    else:
        form = SignupForm()
    return render(request, 'auth/signup.html', {'form': form})

def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # Check if there's a 'next' parameter in the URL (for redirecting to the original page)
            #next_url = request.GET.get('next', 'applicant_dashboard')  # Default to dashboard if 'next' not found

            return redirect('applicant_dashboard')  # Redirect to the 'next' page

    else:
        form = AuthenticationForm()

    return render(request, 'auth/login.html', {'form': form})

# Logout View
def logout_view(request):
    logout(request)
    messages.success(request, "You have logged out.")
    return redirect('landing')

@login_required
@login_required
def applicant_dashboard(request):
    # Check if the logged-in user has an applicant profile
    applicant = Applicant.objects.filter(user=request.user).first()

    if applicant:
        has_applied = True
        # Fetch past application results
        past_results = ApplicationResult.objects.filter(applicant=applicant)
    else:
        has_applied = False
        past_results = None

    return render(request, "dashboard.html", {
        "has_applied": has_applied,
        "past_results": past_results
    })


@login_required
def view_result(request, result_id):
    # Fetch application result or return 404
    result = get_object_or_404(ApplicationResult, id=result_id, applicant__user=request.user)

    # Parse mismatches JSON string into a Python dictionary
    mismatches_data = json.loads(result.mismatches)

    return render(request, "view_results.html", {
        "result": result,
        "mismatches": mismatches_data.get("mismatches", {}),
        "similarities": mismatches_data.get("similarities", {}),
        "missing_fields": mismatches_data.get("missing_fields", []),
        "extra_fields": mismatches_data.get("extra_fields", [])
    })

# View to handle document submission and analysis
@login_required
def submit_application(request):
    if request.method == "POST":
        form = ApplicantForm(request.POST, request.FILES)
        if form.is_valid():
            # Create an applicant instance but don't save yet
            applicant = form.save(commit=False)

            # Manually assign the logged-in user to the user field
            applicant.user = request.user  # Assign the logged-in user to the applicant's user field

            # Now save the applicant object
            applicant.save()

            # Create an ApplicationResult entry for this applicant
            application_result = ApplicationResult.objects.create(
                applicant=applicant
            )

            return redirect('verify_document', applicant_id=applicant.id)  # Redirect to verify documents page
    else:
        form = ApplicantForm()

    return render(request, 'submit_application.html', {'applicant_form': form})

@login_required
def verify_document(request, applicant_id):
    applicant = get_object_or_404(Applicant, id=applicant_id)

    if request.method == "POST":
        document_type = request.POST.get("document_type")  # Get document type selected by user
        
        # Define mapping of document types to model fields
        document_fields = {
            "aadhaar": "aadhaar_document",
            "marksheet": "marksheet_document",
        }
        
        # Get document field name from mapping
        document_field = document_fields.get(document_type)
        
        if not document_field:
            messages.error(request, "Invalid document type selected.")
            return redirect("verify_document", applicant_id=applicant.id)

        # Get the actual document file from the Applicant model
        document_file = getattr(applicant, document_field, None)

        if not document_file:
            messages.error(request, f"{document_type.capitalize()} document not found.")
            return redirect("verify_document", applicant_id=applicant.id)

        document_path = document_file.path

        if not os.path.exists(document_path):
            print(f"❌ {document_type.capitalize()} document file not found: {document_path}")
            return redirect("error")  # Redirect to an error page or handle as necessary

        print(f"📂 Processing {document_type.capitalize()} document: {document_path}")

        try:
            # Step 1: Extract text from document
            extracted_text = extract_text(document_path)

            if not extracted_text.strip():
                print("⚠️ No text extracted from document.")
                messages.error(request, "No readable text extracted from document.")
                return redirect("verify_documents", applicant_id=applicant.id)

            print(f"📝 Extracted Text from {document_type.capitalize()} Document:\n{extracted_text}")

            # Step 2: Prepare expected data based on document type
            expected_data = {}

            if document_type == "aadhaar":
                expected_data = {
                    "name": applicant.name,
                    "date_of_birth": applicant.date_of_birth.strftime("%Y-%m-%d") if applicant.date_of_birth else None,
                    "address": applicant.address,
                    "aadhar_number": applicant.aadhar_number,
                    "phone": applicant.phone,
                }
            elif document_type == "marksheet":
                expected_data = {
                    "name": applicant.name,
                    "date_of_birth": applicant.date_of_birth.strftime("%Y-%m-%d") if applicant.date_of_birth else None,
                    #"roll_number": applicant.roll_number,
                    "university": applicant.university,
                    "course": applicant.course,
                    "year_of_passing": applicant.year_of_passing,
                    "percentage": applicant.percentage,
                }

            # Step 3: Send extracted text & expected data to Gemini API for validation
            gemini_response = send_to_gemini(extracted_text, expected_data)

            if not gemini_response or "error" in gemini_response:
                print("❌ Gemini API response contains an error:", gemini_response.get("error", "Unknown error"))

                messages.error(request, "Error validating document with AI.")
                return redirect("verify_documents", applicant_id=applicant.id)

            # Step 4: Process and save extracted data
            extracted_fields = {str(k): v for k, v in gemini_response.items()}  # Ensure JSON serializability
            applicant.extracted_data = json.dumps(extracted_fields, indent=2)
            applicant.expected_json = json.dumps(expected_data, indent=2)
            applicant.save()

            print(f"✅ Extracted Fields: {json.dumps(extracted_fields, indent=2)}")

            # Step 5: Validate extracted data against expected data
            validation_result = validate_gemini_response(expected_data, extracted_fields)

            # Step 6: Calculate overall mismatch percentage
            total_mismatches = sum(mismatch["Mismatch %"] for mismatch in validation_result["mismatches"].values())
            num_fields = len(expected_data)
            overall_mismatch_percentage = round(total_mismatches / num_fields, 2) if num_fields else 0

            # Step 7: Save ApplicationResult with mismatches
            application_result = ApplicationResult.objects.get(applicant=applicant)
            application_result.mismatches = json.dumps(validation_result, indent=2)
            application_result.mismatch_percentage = overall_mismatch_percentage
            applicant.mismatch_percentage=overall_mismatch_percentage
            application_result.save()

            print(f"🔍 Validation Result: {json.dumps(validation_result, indent=2)}")

            # Step 8: Generate mismatch visualization if mismatches exist
            if validation_result.get("mismatches") or validation_result.get("missing_fields"):
                visualize_mismatches(validation_result, applicant.id)

            messages.success(request, f"{document_type.capitalize()} document verified successfully!")
            return redirect("applicant_results", applicant_id=applicant.id)

        except Exception as e:
            print(f"❌ Error processing document: {e}")
            messages.error(request, "Error processing document.")
            return redirect("verify_document", applicant_id=applicant.id)

    return render(request, "verify_documents.html", {"applicant": applicant})


@login_required
def applicant_results(request, applicant_id):
    # Fetch the associated applicant and result records for the logged-in user
    applicant = get_object_or_404(Applicant, id=applicant_id, user=request.user)  # Ensure it's the correct user
    application_result = get_object_or_404(ApplicationResult, applicant=applicant)

    # Handle extracted data and mismatches as before
    extracted_data = json.loads(applicant.extracted_data) if applicant.extracted_data else {}
    expected_data = json.loads(applicant.expected_json) if applicant.expected_json else {}
    mismatches = json.loads(application_result.mismatches) if application_result.mismatches else {}

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
        application_result.mismtach_plot=mismatch_plot_path
        if mismatch_plot_path:
            mismatch_plot_url = settings.MEDIA_URL + os.path.basename(mismatch_plot_path)

    return render(request, "results.html", {
        "applicant": applicant,
        "extracted_data": extracted_data,
        "expected_data": expected_data,
        "mismatches": formatted_mismatches,
        "mismatch_plot_path": mismatch_plot_url
    })
