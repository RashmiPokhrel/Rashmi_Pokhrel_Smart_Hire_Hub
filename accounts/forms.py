from django import forms

class RegisterForm(forms.Form):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'placeholder': 'Username'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder': 'Email'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))
    role = forms.ChoiceField(choices=[('jobseeker', 'Job Seeker'), ('recruiter', 'Recruiter')])

    # Recruiter fields
    company_name = forms.CharField(max_length=200, required=False)
    company_email = forms.EmailField(required=False)
    company_phone = forms.CharField(max_length=20, required=False)
    company_address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)