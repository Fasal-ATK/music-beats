from django import forms
from django.forms import ModelForm
from .models import Product, Category


class ProductForm(ModelForm):
    class Meta:
        model = Product
        fields = ['title', 'price', 'category', 'description', 'image', 'stock']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'cols': 40}),
        }

class CategoryForm(ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']