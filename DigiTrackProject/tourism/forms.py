from django import forms

class ChangePasswordForm(forms.Form):
    current_password = forms.CharField(widget=forms.PasswordInput, required=True)
    new_password1 = forms.CharField(widget=forms.PasswordInput, required=True)
    new_password2 = forms.CharField(widget=forms.PasswordInput, required=True)

    def clean(self):
        cleaned = super().clean()
        n1 = cleaned.get('new_password1')
        n2 = cleaned.get('new_password2')
        if n1 and n2 and n1 != n2:
            raise forms.ValidationError('New passwords do not match.')
        if n1 and len(n1) < 8:
            raise forms.ValidationError('New password must be at least 8 characters long.')
        return cleaned
