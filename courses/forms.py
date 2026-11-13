from django import forms
from django.core.exceptions import ValidationError
from .models import Submission, PaymentSubmission

_ALLOWED_SUBMISSION_EXTENSIONS = {'jpg', 'jpeg', 'png', 'psd', 'mp4', 'zip'}
_MAX_SUBMISSION_SIZE = 50 * 1024 * 1024  # 50 MB

class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['file']
        widgets = {
            'file': forms.FileInput(attrs={'class': 'form-control glass', 'accept': '.jpg,.jpeg,.png,.psd,.mp4,.zip'})
        }

    def clean_file(self):
        f = self.cleaned_data.get('file')
        if f:
            ext = f.name.rsplit('.', 1)[-1].lower() if '.' in f.name else ''
            if ext not in _ALLOWED_SUBMISSION_EXTENSIONS:
                raise ValidationError(
                    f"File type '.{ext}' is not allowed. "
                    f"Allowed types: {', '.join(sorted(_ALLOWED_SUBMISSION_EXTENSIONS))}"
                )
            if f.size > _MAX_SUBMISSION_SIZE:
                raise ValidationError("File size exceeds the 50 MB limit.")
        return f


class PaymentSubmissionForm(forms.ModelForm):
    class Meta:
        model = PaymentSubmission
        fields = ['utr_reference', 'proof_image']
        widgets = {
            'utr_reference': forms.TextInput(attrs={
                'class': 'form-control glass',
                'placeholder': 'e.g. 402913827491 (from your UPI app)',
            }),
            'proof_image': forms.FileInput(attrs={
                'class': 'form-control glass',
                'accept': '.jpg,.jpeg,.png,.webp',
            }),
        }

    def clean_proof_image(self):
        f = self.cleaned_data.get('proof_image')
        if f:
            ext = f.name.rsplit('.', 1)[-1].lower() if '.' in f.name else ''
            if ext not in {'jpg', 'jpeg', 'png', 'webp'}:
                raise forms.ValidationError("Please upload a screenshot image (JPG, PNG, or WEBP).")
            if f.size > 5 * 1024 * 1024:
                raise forms.ValidationError("Image is too large (max 5 MB).")
        return f
