from django.db.models import Q
from django import forms
from .models import CoffeeBag, Brew



class BrewForm(forms.ModelForm):
    coffee_bag = forms.ModelChoiceField(queryset=CoffeeBag.objects.filter(end_date__isnull=True))

    def __init__(self, *args, **kwargs):
        super(BrewForm, self).__init__(*args, **kwargs)
        if self.instance.pk is not None:
            self.fields['coffee_bag'].queryset = CoffeeBag.objects.filter(
                Q(end_date__isnull=True)|Q(id=self.instance.coffee_bag_id)
            )

    class Meta:
        model = Brew
        exclude = ['id']
