from django import forms

from .models import WORKING_AREA_DEPARTEMENT, Transporteur


class SubscriptionForm(forms.ModelForm):
    class Meta:
        model = Transporteur
        fields = [
            'email',
            'telephone',
            'working_area',
            'working_area_departements',
            'specialities',
            'website',
        ]

    def clean(self):
        cleaned_data = super().clean()
        if (cleaned_data.get('working_area') == WORKING_AREA_DEPARTEMENT and
                len(cleaned_data.get('working_area_departements', [])) == 0):
            self.add_error(
                'working_area_departements',
                "Des départements doivent être renseignés quand l'aire de travail est départementale."
            )
