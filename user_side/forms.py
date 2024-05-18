from django import forms
from .models import Address


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['name', 'address_line', 'phone', 'city', 'state', 'postal_code', 'country']
        widgets = {
            'address_line': forms.Textarea(attrs={'rows': 3}),
        }
    