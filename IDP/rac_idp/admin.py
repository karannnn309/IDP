from django.contrib import admin
from .models import *




class ApplicantAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'name', 'date_of_birth', 'phone', 'email', 'caste_category', 'aadhar_number', 
        'university', 'course', 'year_of_passing', 'percentage', 'work_experience', 'mismatch_percentage'
    )
    search_fields = ('name', 'email', 'aadhar_number', 'phone')
    list_filter = ('date_of_birth', 'caste_category', 'university', 'course', 'year_of_passing')
    ordering = ('-date_of_birth',)
    # Display fields with the option to view and edit them in the admin
    fields = (
        'user', 'name', 'date_of_birth', 'phone', 'address', 'email', 'caste_category', 'aadhar_number',
        'aadhaar_document', 'ews_certificate', 'caste_certificate', 'income_certificate',
        'university', 'course', 'year_of_passing', 'percentage', 'marksheet_document', 
        'work_experience', 'experience_certificate', 'extracted_data', 'expected_json', 'mismatches', 'mismatch_percentage'
    )

class ApplicationResultAdmin(admin.ModelAdmin):
    list_display = ('applicant', 'application_date',  'mismatches')
    search_fields = ('applicant__name', 'applicant__email')
    list_filter = ('application_date',)
    ordering = ('application_date',)
    list_per_page = 20


admin.site.register(Applicant, ApplicantAdmin)
admin.site.register(ApplicationResult, ApplicationResultAdmin)



