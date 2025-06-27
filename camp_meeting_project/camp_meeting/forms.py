# forms.py
from django import forms
from .models import Contribution

class ContributionForm(forms.ModelForm):
    """Form for handling contributions"""
    
    class Meta:
        model = Contribution
        fields = ['full_name', 'phone_number', 'email', 'amount']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Enter full name',
                'required': True
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': '254700000000',
                'required': True,
                'pattern': '^(\+254|254|0)[17]\d{8}$',
                'title': 'Please enter a valid Kenyan phone number'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Enter your email address',
                'required': True
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Enter amount (Ksh)',
                'min': '1',
                'step': '1',
                'required': True
            })
        }
        
    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        
        # Remove any spaces or special characters
        phone_number = ''.join(filter(str.isdigit, phone_number))
        
        # Format phone number
        if phone_number.startswith('0') and len(phone_number) == 10:
            phone_number = '254' + phone_number[1:]
        elif phone_number.startswith('254') and len(phone_number) == 12:
            pass  # Already in correct format
        else:
            raise forms.ValidationError('Please enter a valid Kenyan phone number')
        
        return phone_number
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and "@" not in email:
            raise forms.ValidationError('Please enter a valid email address')
        return email
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        
        if amount < 1:
            raise forms.ValidationError('Amount must be at least Ksh. 1')
        
        if amount > 1000000:
            raise forms.ValidationError('Amount cannot exceed Ksh. 1,000,000')
        
        return amount