from django.db import models

# Create your models here.
class Applicant(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=255,unique=False)
    phone = models.CharField(max_length=15)
    extracted_data = models.JSONField(null=True, blank=True)  # Stores extracted data from Gemini
    expected_json = models.JSONField(null=True, blank=True)   # Stores expected form data
    mismatches = models.JSONField(null=True, blank=True)
    mismatch_percentage = models.FloatField(default=0)  # 🔹 Store mismatch %      # Stores mismatches
    #form_data = models.JSONField(null=False,default="NA")  # Store form data as JSON

    def __str__(self):
        return self.name

class Document(models.Model):
    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE, related_name="documents")
    file = models.FileField(upload_to="documents/")
    extracted_text = models.JSONField(null=True, blank=True)  # Store extracted text
    mismatches = models.JSONField(null=True, blank=True)  # Store mismatches

    def __str__(self):
        return f"{self.applicant.name} - {self.file.name} "