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
            'description',
            'edit_code'
        ]

    def __init__(self, data, transporteur):
        super().__init__(data)
        self.transporteur = transporteur

    def clean_working_area_departements(self):
        """Pads departement numbers lesser than 10 with a zero"""
        formated_departements = []
        departements = self.cleaned_data.get('working_area_departements')
        for departement in departements:
            formated_departements.append('{:0>2}'.format(departement))
        # Unique and sorted
        return sorted(set(formated_departements))

    def clean_edit_code(self):
        # Access control to locked transporteur
        edit_code = self.cleaned_data.get('edit_code')
        if not self.transporteur.check_edit_code(edit_code):
            raise forms.ValidationError("Le code de modification n'est pas valide.")

        return edit_code

    def clean(self):
        cleaned_data = super().clean()
        if (cleaned_data.get('working_area') == WORKING_AREA_DEPARTEMENT and
                not cleaned_data.get('working_area_departements', [])):
            self.add_error(
                'working_area_departements',
                "Des départements doivent être renseignés quand l'aire de travail est départementale."
            )
