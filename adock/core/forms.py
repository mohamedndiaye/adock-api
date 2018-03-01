from django import forms

from .models import Carrier


class SubscriptionForm(forms.ModelForm):
    class Meta:
        model = Carrier
        fields = ['siret', 'email', 'phone']
