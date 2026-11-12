# catalog/forms.py
from django import forms

class MapSearchForm(forms.Form):
    query = forms.CharField(
        required=False, 
        widget=forms.TextInput(attrs={'placeholder': 'Search places (e.g., Harrisonburg)...'})
    )
    year = forms.IntegerField(
        required=False, 
        widget=forms.NumberInput(attrs={'placeholder': 'Year'})
    )
    # Optional: basic coordinate search (point inside the bounds)
    lat = forms.FloatField(required=False, widget=forms.NumberInput(attrs={'placeholder': 'Latitude'}))
    lng = forms.FloatField(required=False, widget=forms.NumberInput(attrs={'placeholder': 'Longitude'}))