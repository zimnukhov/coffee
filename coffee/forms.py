from django import forms
from .models import Brew



class BrewForm(forms.ModelForm):
    class Meta:
        model = Brew
        exclude = ['id']
