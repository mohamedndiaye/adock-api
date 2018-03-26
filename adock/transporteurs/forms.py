from django import forms

from .models import Transporteur


class SubscriptionForm(forms.ModelForm):
    class Meta:
        model = Transporteur
        fields = ['email', 'telephone', 'working_area', 'working_area_departements']
