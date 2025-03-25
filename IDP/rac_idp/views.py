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
import random
from django.core.mail import send_mail
from django.utils.timezone import now
from django.http import HttpResponseBadRequest, HttpResponseServerError
from django.core.exceptions import ValidationError
import logging
from django.core.mail import EmailMessage
import time

logger = logging.getLogger(__name__)

# Generate OTP
def generate_otp():
    return str(random.randint(100000, 999999))

# views.py

# views.py
from django.core.mail import send_mail
from django.conf import settings

def send_otp_email(user, otp_code):
    subject = "Your OTP Code"
    message = f"Your verification code is: {otp_code}"
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user.email]
    
    try:
        send_mail(
            subject,
            message,
            from_email,
            recipient_list,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def landing_page(request):
    return render(request, "landing.html")

def signup_view(request):
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                login(request, user)
                Applicant.objects.create(user=user)
                messages.success(request, "Account created successfully! Please log in.")
                return redirect('login')
            except Exception as e:
                logger.error(f"Error during signup: {e}")
                messages.error(request, "An error occurred during signup. Please try again.")
        else:
            logger.warning(f"Signup form errors: {form.errors}")
            messages.error(request, "Please correct the errors below.")
    else:
        form = SignupForm()
    return render(request, 'auth/signup.html', {'form': form})

# views.py
def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            otp_code = generate_otp()
            
            # Save OTP to database
            OTP.objects.update_or_create(
                user=user, 
                defaults={"code": otp_code, "created_at": now()}
            )
            
            # Send OTP via email
            if send_otp_email(user, otp_code):
                request.session["otp_user_id"] = user.id
                return redirect("otp_verification")
            else:
                messages.error(request, "Failed to send OTP. Please try again.")
    
    return render(request, 'auth/login.html', {'form': AuthenticationForm()})
def otp_verification_view(request):
    user_id = request.session.get("otp_user_id")
    if not user_id:
        messages.error(request, "OTP session expired or invalid.")
        return redirect("login")

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, "Invalid user.")
        return redirect("login")

    if request.method == "POST":
        otp_entered = request.POST.get("otp", "").strip()
        if not otp_entered:
            messages.error(request, "Please enter the OTP.")
            return render(request, "auth/otp_verification.html")

        # Check database OTP first
        otp_instance = OTP.objects.filter(user=user).first()
        
        # If no DB OTP or it's invalid, check session fallback
        if not otp_instance or not otp_instance.is_valid():
            fallback_otp = request.session.get('fallback_otp')
            if fallback_otp and fallback_otp == otp_entered:
                login(request, user)
                del request.session["otp_user_id"]
                del request.session["fallback_otp"]
                messages.success(request, "Logged in successfully! (via fallback OTP)")
                return redirect("applicant_dashboard")
            else:
                messages.error(request, "Invalid or expired OTP.")
                return render(request, "auth/otp_verification.html")
        
        # Normal OTP verification
        if otp_instance.code == otp_entered:
            login(request, user)
            otp_instance.delete()
            del request.session["otp_user_id"]
            if 'fallback_otp' in request.session:
                del request.session["fallback_otp"]
            messages.success(request, "Logged in successfully!")
            return redirect("applicant_dashboard")
        else:
            messages.error(request, "Invalid OTP. Please try again.")

    return render(request, "auth/otp_verification.html")

def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('landing')

@login_required
def applicant_dashboard(request):
    try:
        applicant = Applicant.objects.get(user=request.user)
        has_applied = ApplicationResult.objects.filter(applicant=applicant).exists()
        past_results = ApplicationResult.objects.filter(applicant=applicant) if has_applied else None
        
        return render(request, "dashboard.html", {
            "has_applied": has_applied,
            "past_results": past_results
        })
    except Applicant.DoesNotExist:
        messages.error(request, "Applicant profile not found.")
        return redirect('landing')

@login_required
def submit_application(request):
    try:
        applicant = Applicant.objects.get(user=request.user)
    except Applicant.DoesNotExist:
        applicant = None

    if request.method == 'POST':
        form = ApplicantForm(request.POST, request.FILES, instance=applicant)
        if form.is_valid():
            try:
                applicant = form.save(commit=False)
                applicant.user = request.user
                applicant.save()
                messages.success(request, "Application submitted successfully!")
                return redirect('verify_document', applicant_id=applicant.id)
            except Exception as e:
                logger.error(f"Error saving application: {e}")
                messages.error(request, "An error occurred while saving your application.")
        else:
            logger.warning(f"Application form errors: {form.errors}")
            messages.error(request, "Please correct the errors below.")
    else:
        form = ApplicantForm(instance=applicant)

    return render(request, 'submit_application.html', {'applicant_form': form})

@login_required
def verify_document(request, applicant_id):
    try:
        applicant = Applicant.objects.get(id=applicant_id, user=request.user)
    except Applicant.DoesNotExist:
        messages.error(request, "Applicant not found.")
        return redirect('applicant_dashboard')

    # Get or create application result
    application_result, created = ApplicationResult.objects.get_or_create(applicant=applicant)

    if request.method == "POST":
        document_type = request.POST.get("document_type")
        
        if not document_type or document_type not in ["aadhaar", "marksheet"]:
            messages.error(request, "Invalid document type selected.")
            return redirect("verify_document", applicant_id=applicant.id)

        # Map document type to model field
        document_field_map = {
            "aadhaar": "aadhaar_document",
            "marksheet": "marksheet_document",
        }
        
        document_field = document_field_map.get(document_type)
        document_file = getattr(applicant, document_field, None)
        
        if not document_file:
            messages.error(request, f"{document_type.capitalize()} document not uploaded.")
            return redirect("verify_document", applicant_id=applicant.id)

        try:
            document_path = document_file.path
            if not os.path.exists(document_path):
                logger.error(f"Document file not found: {document_path}")
                messages.error(request, "Document file not found. Please re-upload.")
                return redirect("verify_document", applicant_id=applicant.id)

            # Extract text from document
            extracted_text = extract_text(document_path)
            if not extracted_text.strip():
                messages.error(request, "No readable text extracted from document.")
                return redirect("verify_document", applicant_id=applicant.id)

            # Prepare expected data based on document type
            expected_data = {
                "aadhaar": {
                    "name": applicant.name,
                    "date_of_birth": applicant.date_of_birth.strftime("%Y-%m-%d") if applicant.date_of_birth else None,
                    "address": applicant.address,
                    "aadhar_number": applicant.aadhar_number,
                    "phone": applicant.phone,
                },
                "marksheet": {
                    "name": applicant.name,
                    "date_of_birth": applicant.date_of_birth.strftime("%Y-%m-%d") if applicant.date_of_birth else None,
                    "university": applicant.university,
                    "course": applicant.course,
                    "year_of_passing": applicant.year_of_passing,
                    "percentage": applicant.percentage,
                }
            }.get(document_type, {})

            # Send to Gemini API for validation
            gemini_response = send_to_gemini(extracted_text, expected_data)
            if not gemini_response or "error" in gemini_response:
                logger.error(f"Gemini API error: {gemini_response.get('error', 'Unknown error')}")
                messages.error(request, "Error validating document with AI.")
                return redirect("verify_document", applicant_id=applicant.id)

            # Process and save extracted data
            extracted_fields = {str(k): v for k, v in gemini_response.items()}
            applicant.extracted_data = json.dumps(extracted_fields, indent=2)
            applicant.expected_json = json.dumps(expected_data, indent=2)
            
            # Validate and calculate mismatches
            validation_result = validate_gemini_response(expected_data, extracted_fields)
            total_mismatches = sum(mismatch.get("Mismatch %", 0) 
                           for mismatch in validation_result.get("mismatches", {}).values())
            num_fields = len(expected_data)
            overall_mismatch_percentage = round(total_mismatches / num_fields, 2) if num_fields else 0

            # Save results
            application_result.mismatches = json.dumps(validation_result, indent=2)
            application_result.mismatch_percentage = overall_mismatch_percentage
            applicant.mismatch_percentage = overall_mismatch_percentage
            
            applicant.save()
            application_result.save()

            # Generate visualization if needed
            if validation_result.get("mismatches") or validation_result.get("missing_fields"):
                visualize_mismatches(validation_result, applicant.id)

            messages.success(request, f"{document_type.capitalize()} document verified successfully!")
            return redirect("applicant_results", applicant_id=applicant.id)

        except Exception as e:
            logger.error(f"Error processing document: {e}")
            messages.error(request, "An error occurred while processing your document.")
            return redirect("verify_document", applicant_id=applicant.id)

    return render(request, "verify_documents.html", {"applicant": applicant})

@login_required
def applicant_results(request, applicant_id):
    try:
        applicant = Applicant.objects.get(id=applicant_id, user=request.user)
        application_result = ApplicationResult.objects.get(applicant=applicant)
    except (Applicant.DoesNotExist, ApplicationResult.DoesNotExist) as e:
        messages.error(request, "Results not found.")
        return redirect('applicant_dashboard')

    try:
        extracted_data = json.loads(applicant.extracted_data) if applicant.extracted_data else {}
        expected_data = json.loads(applicant.expected_json) if applicant.expected_json else {}
        mismatches = json.loads(application_result.mismatches) if application_result.mismatches else {}
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        messages.error(request, "Error loading results data.")
        return redirect('applicant_dashboard')

    # Format mismatches for template
    formatted_mismatches = []
    for field, details in mismatches.get("mismatches", {}).items():
        formatted_mismatches.append({
            "field": field,
            "expected": details.get("Expected", ""),
            "extracted": details.get("Extracted", ""),
            "mismatch_percentage": details.get("Mismatch %", 0),
        })

    # Generate plot URL if exists
    mismatch_plot_url = None
    if application_result.mismatch_plot_path:
        mismatch_plot_url = settings.MEDIA_URL + os.path.basename(application_result.mismatch_plot_path)

    return render(request, "results.html", {
        "applicant": applicant,
        "extracted_data": extracted_data,
        "expected_data": expected_data,
        "mismatches": formatted_mismatches,
        "mismatch_plot_url": mismatch_plot_url,
        "overall_mismatch": application_result.mismatch_percentage
    })

@login_required
def view_result(request, result_id):
    try:
        result = ApplicationResult.objects.get(id=result_id, applicant__user=request.user)
        mismatches_data = json.loads(result.mismatches) if result.mismatches else {}
    except (ApplicationResult.DoesNotExist, json.JSONDecodeError) as e:
        messages.error(request, "Result not found or invalid.")
        return redirect('applicant_dashboard')

    return render(request, "view_results.html", {
        "result": result,
        "mismatches": mismatches_data.get("mismatches", {}),
        "similarities": mismatches_data.get("similarities", {}),
        "missing_fields": mismatches_data.get("missing_fields", []),
        "extra_fields": mismatches_data.get("extra_fields", [])
    })

# views.py
from django.http import HttpResponse

def test_email(request):
    send_mail(
        'Test Subject',
        'Test message body.',
        settings.EMAIL_HOST_USER,
        ['recipient@gmail.com'],  # Your test email
        fail_silently=False,
    )
    return HttpResponse("Test email sent - check your inbox!")
