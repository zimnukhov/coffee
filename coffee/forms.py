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

        split = value.split(':', 2)

        hours = 0
        if len(split) == 3:
            if not split[0].isdigit():
                raise forms.ValidationError('Incorrect hours value')
            hours = int(split[0])
            minutes_str = split[1]
            seconds_str = split[2]
        elif len(split) == 2:
            minutes_str = split[0]
            seconds_str = split[1]
        else:
            raise forms.ValidationError('Incorrect duration format')

        if not minutes_str.isdigit():
            raise forms.ValidationError('Incorrect minutes value')

        minutes = int(minutes_str)

        if hours > 0 and minutes > 59:
            raise forms.ValidationError('Minutes value out of range')

        if not seconds_str.isdigit():
            raise forms.ValidationError('Incorrect seconds value')

        seconds = int(seconds_str)

        if seconds > 59:
            raise forms.ValidationError('Seconds value out of range')

        return hours * 3600 + minutes * 60 + seconds


class BrewForm(forms.ModelForm):
    coffee_bag = forms.ModelChoiceField(queryset=CoffeeBag.objects.filter(status=CoffeeBag.NOT_FINISHED))
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
        labels = {
            'water_tds': 'TDS',
        }
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 4, 'cols': 35}),
            'extraction': forms.RadioSelect(),
        }


class BrewRatingForm(forms.ModelForm):
    class Meta:
        model = Brew
        fields = ['rating']


class CoffeeBagForm(forms.ModelForm):
    class Meta:
        model = CoffeeBag
        exclude = ['id', 'thumbnail']
        widgets = {
            'roaster_comment': forms.TextInput(),
        }
