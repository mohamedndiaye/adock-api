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

    def clean_working_area_departements(self):
        """Pads departement numbers lesser than 10 with a zero"""
        formated_departements = []
        departements = self.cleaned_data['working_area_departements']
        for departement in departements:
            formated_departements.append('{:0>2}'.format(departement))
        return formated_departements

    def clean(self):
        cleaned_data = super().clean()
        if (cleaned_data.get('working_area') == WORKING_AREA_DEPARTEMENT and
                len(cleaned_data.get('working_area_departements', [])) == 0):
            self.add_error(
                'working_area_departements',
                "Des départements doivent être renseignés quand l'aire de travail est départementale."
            )
