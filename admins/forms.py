from django import forms
from django.forms import ModelForm
from django.core.exceptions import ValidationError
from .models import Product, Category,Brand

 
class ProductForm(ModelForm):
    class Meta:
        model = Product
        fields = ['title', 'price', 'category', 'description', 'image', 'stock']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'cols': 40}),
            'image': forms.ClearableFileInput(attrs={'class': 'custom-file-input'}),
        }
    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is not None and price < 0:
            raise ValidationError("Price must be a non-negative number.")
        return price


class CategoryForm(ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']


class BrandForm(forms.ModelForm):
    class Meta:
        model = Brand
        fields = ['name', 'logo']
        widgets = {
            'logo': forms.ClearableFileInput(attrs={'class': 'custom-file-input'})
        }