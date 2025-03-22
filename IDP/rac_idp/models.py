# models.py
from django.db import models
from django.contrib.auth.models import User  # Use the default User model
from django.conf import settings

class Applicant(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True,unique=False)  # Foreign key to the User model
    name = models.CharField(max_length=255, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    phone = models.CharField(max_length=15, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    email = models.EmailField(max_length=50, null=True, blank=True)
    caste_category = models.CharField(max_length=10, null=True, blank=True)
    aadhar_number = models.IntegerField(null=True, blank=True)

    # Uploaded documents
    aadhaar_document = models.FileField(upload_to="documents/aadhaar/", null=True, blank=True)
    ews_certificate = models.FileField(upload_to="documents/ews/", null=True, blank=True)
    caste_certificate = models.FileField(upload_to="documents/caste/", null=True, blank=True)
    income_certificate = models.FileField(upload_to="documents/income/", null=True, blank=True)

    # Academic Information
    university = models.CharField(max_length=255, null=True, blank=True)
    course = models.CharField(max_length=255, null=True, blank=True)
    year_of_passing = models.IntegerField(null=True)
    percentage = models.FloatField(null=True, blank=True)
    marksheet_document = models.FileField(upload_to="documents/income/", null=True, blank=True)

    # Work Experience (Optional)
    work_experience = models.TextField(null=True, blank=True)
    experience_certificate = models.FileField(upload_to="documents/experience/", null=True, blank=True)

    # Extracted Data & Verification
    extracted_data = models.JSONField(null=True, blank=True)
    expected_json = models.JSONField(null=True, blank=True)
    mismatches = models.JSONField(null=True, blank=True)
    mismatch_percentage = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.name if self.name else f"Applicant {self.id}"
    
class ApplicationResult(models.Model):
    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE,null=True, blank=True)
    application_date = models.DateTimeField(auto_now_add=True)
    mismatches = models.JSONField(null=True, blank=True)  # Or create a Mismatch model
    mismatch_percentage=models.FloatField(null=True,blank=False)
    mismatch_plot_path = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"Result for {self.applicant.name} - {self.application_date}"
