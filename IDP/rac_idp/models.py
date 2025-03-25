# models.py
from django.db import models
from django.contrib.auth.models import User

class Applicant(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)  # Foreign key to User model
    name = models.CharField(max_length=255, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    phone = models.CharField(max_length=15, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    caste_category = models.CharField(max_length=10, null=True, blank=True)
    aadhar_number = models.CharField(max_length=12, null=True, blank=True)  # Changed to CharField to avoid integer issues

    # Uploaded Documents
    aadhaar_document = models.FileField(upload_to="documents/aadhaar/", null=True, blank=True)
    ews_certificate_document = models.FileField(upload_to="documents/ews/", null=True, blank=True)
    caste_certificate_document = models.FileField(upload_to="documents/caste/", null=True, blank=True)
    income_certificate_document = models.FileField(upload_to="documents/income/", null=True, blank=True)
    marksheet_document = models.FileField(upload_to="documents/marksheet/", null=True, blank=True)  # Fixed path

    # Academic Information
    university = models.CharField(max_length=255, null=True, blank=True)
    course = models.CharField(max_length=255, null=True, blank=True)
    year_of_passing = models.IntegerField(null=True)
    percentage = models.FloatField(null=True, blank=True)

    # Work Experience (Optional)
    work_experience = models.TextField(null=True, blank=True)
    experience_certificate = models.FileField(upload_to="documents/experience/", null=True, blank=True)

    # Extracted Data & Verification
    extracted_data = models.JSONField(null=True, blank=True)
    expected_json = models.JSONField(null=True, blank=True)
    mismatches = models.JSONField(null=True, blank=True)
    mismatch_percentage = models.FloatField(null=True, blank=True)

    def _str_(self):
        return self.name if self.name else f"Applicant {self.id}"


class ApplicationResult(models.Model):
    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE)
    application_date = models.DateTimeField(auto_now_add=True)
    mismatches = models.JSONField(null=True, blank=True)
    mismatch_percentage = models.FloatField(null=True, blank=True)
    mismatch_plot_path = models.CharField(max_length=255, null=True, blank=True)  # Retained for visualization

    def _str_(self):
        return f"Result for {self.applicant.name} - {self.application_date}"
