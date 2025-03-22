from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import *

class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=15, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'password1', 'password2']


# Applicant Form
class ApplicantForm(forms.ModelForm):
    class Meta:
        model = Applicant
        fields = [
            'name', 'date_of_birth', 'phone', 'address', 'caste_category', 'aadhar_number',
            'aadhaar_document', 'ews_certificate', 'caste_certificate', 'income_certificate',
            'marksheet_document', 'university', 'course', 'year_of_passing', 'percentage',
            'work_experience', 'experience_certificate'
        ]
        
    def __init__(self, *args, **kwargs):
        super(ApplicantForm, self).__init__(*args, **kwargs)
        # Add validation to check for documents if needed (optional)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'  # Adding Bootstrap class for styling
   
