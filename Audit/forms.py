from django import forms
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe
from .models import Category, UserCategory
from django.forms.widgets import SelectMultiple

# from django.utils.translation import gettext_lazy as _

class MultiSelect(SelectMultiple):
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(
            name, value, label, selected, index, subindex=subindex, attrs=attrs
        )

        # value.instance is available for ModelChoiceField
        if hasattr(value, "instance"):
            obj = value.instance
            option["attrs"].update({
                "data-depth": obj.depth,
                "data-parent": obj.parent_id or "",
            })

        return option

class UserCategoryForm(forms.ModelForm):
    class Meta:
        model = UserCategory
        fields = [
            'category',
        ]
        labels = {
            'category': 'Categories',
        }
        widgets = {
            'category': MultiSelect(attrs={'class': 'form-control'}),
        }
