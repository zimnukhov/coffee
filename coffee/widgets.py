import pprint
from django import forms

class MultiSelectCheckboxWidget(forms.Widget):
    template_name = "coffee/widgets/multiselect_widget.html"

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)

        if value is None:
            value = []
        elif isinstance(value, str):
            value = [value]

        context["widget"]["options"] = list(self.choices)
        context["widget"]["selected_values"] = value
        return context

    def value_from_datadict(self, data, files, name):
        return data.getlist(name)
