from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import *

class SignupForm(UserCreationForm):
    email = forms.EmailField()
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super(SignupForm, self).__init__(*args, **kwargs)
        
        # Add 'form-control' class to each field
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['email'].widget.attrs.update({'class': 'form-control'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
    
class LoginForm(forms.Form):
    username = forms.CharField(max_length=255)
    password = forms.CharField(widget=forms.PasswordInput)


# Applicant Form
class ApplicantForm(forms.ModelForm):
    ews_choice = [
        ('yes', 'Yes'),
        ('no', 'No')
    ]
    ews = forms.ChoiceField(choices=ews_choice, widget=forms.RadioSelect(), required=True)

    # Set the user (CustomUser) while creating the applicant form
   

    class Meta:
        model = Applicant
        fields = [
             'user','name', 'email', 'phone', 'date_of_birth', 'address',
            'caste_category', 'aadhar_number', 'aadhaar_document', 'ews_certificate', 
            'caste_certificate', 'income_certificate', 'university', 'course', 
            'year_of_passing', 'percentage', 'marksheet_document', 'work_experience', 
            'experience_certificate'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
            'aadhaar_document': forms.ClearableFileInput(attrs={'accept': '/pdf,image/*'}),
            'ews_certificate': forms.ClearableFileInput(attrs={'accept': '/pdf,image/*'}),
            'caste_certificate': forms.ClearableFileInput(attrs={'accept': '/pdf,image/*'}),
            'income_certificate': forms.ClearableFileInput(attrs={'accept': '/pdf'}),
            'marksheet_document': forms.ClearableFileInput(attrs={'accept': '/pdf,image/'}),
            'experience_certificate': forms.ClearableFileInput(attrs={'accept': '/pdf'}),
        }

   
