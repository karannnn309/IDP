from django.contrib import admin
from .models import Applicant, Document

@admin.register(Applicant)
class ApplicantAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone", "mismatch_percentage")  # Fields to display in the admin panel
    search_fields = ("name", "email", "phone")  # Enable search functionality
    list_filter = ("mismatch_percentage",)  # Enable filtering options

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("applicant", "file")  # Display applicant name and file name
    search_fields = ("applicant__name",)  # Search by applicant's name
    list_filter = ("applicant",)  # Filter by applicant

