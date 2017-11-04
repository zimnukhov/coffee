from django.db.models import Q
from django import forms
from .models import CoffeeBag, Brew
from .utils import get_time_display


class DurationWidget(forms.TextInput):
    def format_value(self, value):
        if isinstance(value, str):
            return value
        if value:
            return get_time_display(value)
        return ''


class DurationField(forms.CharField):
    def to_python(self, value):
        if not value:
            return None

        if ':' not in value:
            raise forms.ValidationError('Incorrect format for duration')

        split = value.split(':', 1)

        if not split[0].isdigit():
            raise forms.ValidationError('Incorrect minutes value')
        minutes = int(split[0])

        if not split[1].isdigit():
            raise forms.ValidationError('Incorrect seconds value')

        seconds = int(split[1])

        if seconds > 59:
            raise forms.ValidationError('Seconds value out of range')

        return minutes * 60 + seconds


class BrewForm(forms.ModelForm):
    coffee_bag = forms.ModelChoiceField(queryset=CoffeeBag.objects.filter(end_date__isnull=True))
    brew_time = DurationField(widget=DurationWidget, required=False)

    def __init__(self, *args, **kwargs):
        super(BrewForm, self).__init__(*args, **kwargs)
        if self.instance.pk is not None:
            self.fields['coffee_bag'].queryset = CoffeeBag.objects.filter(
                Q(end_date__isnull=True)|Q(id=self.instance.coffee_bag_id)
            )

    class Meta:
        model = Brew
        exclude = ['id']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 4, 'cols': 35}),
        }


class BrewRatingForm(forms.ModelForm):
    class Meta:
        model = Brew
        fields = ['rating']
