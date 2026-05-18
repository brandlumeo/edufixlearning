from django import forms
from django.core.exceptions import ValidationError
from .models import Submission

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
