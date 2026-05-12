from django import forms
from .models import Submission

class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['file']
        widgets = {
            'file': forms.FileInput(attrs={'class': 'form-control glass', 'accept': '.jpg,.png,.psd,.mp4,.zip'})
        }
