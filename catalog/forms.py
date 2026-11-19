# catalog/forms.py
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class MapSearchForm(forms.Form):
    query = forms.CharField(
        label=_("Search by place"),
        required=False,
        widget=forms.TextInput(
            attrs={"placeholder": "Search places (e.g., Harrisonburg)..."}
        ),
    )
    year = forms.IntegerField(
        label=_("Year"),
        required=False,
        widget=forms.NumberInput(
            attrs={
                "placeholder": "Year",
                "min": "1000",
                "max": "9999",
                "oninvalid": "this.setCustomValidity('Please enter a valid 4-digit year.')",
                "oninput": "this.setCustomValidity('')",
            }
        ),
    )
    lat = forms.FloatField(
        label=_("Latitude"),
        required=False,
        widget=forms.NumberInput(
            attrs={
                "placeholder": "Latitude",
                "min": "-90",
                "max": "90",
                "step": "any",  # Allows decimals
                "oninvalid": "this.setCustomValidity('Latitude must be between -90 and 90 degrees.')",
                "oninput": "this.setCustomValidity('')",
            }
        ),
    )
    lng = forms.FloatField(
        label=_("Longitude"),
        required=False,
        widget=forms.NumberInput(
            attrs={
                "placeholder": "Longitude",
                "min": "-180",
                "max": "180",
                "step": "any",  # Allows decimals
                "oninvalid": "this.setCustomValidity('Longitude must be between -180 and 180 degrees.')",
                "oninput": "this.setCustomValidity('')",
            }
        ),
    )

    # You should still keep your clean() methods below this as a backend security fallback!
    # ...
