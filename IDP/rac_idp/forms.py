from django import forms
from .models import Applicant, Document

class ApplicantForm(forms.ModelForm):
    class Meta:
        model = Applicant
        fields = ['name' , 'email', 'phone']

class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['file']