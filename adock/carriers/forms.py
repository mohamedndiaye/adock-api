from django import forms

from .models import WORKING_AREA_DEPARTEMENT, Carrier


class SubscriptionForm(forms.ModelForm):
    class Meta:
        model = Carrier
        fields = [
            "email",
            "telephone",
            "working_area",
            "working_area_departements",
            "specialities",
            "website",
            "description",
            "edit_code",
        ]

    def __init__(self, data, carrier):
        super().__init__(data)
        self.carrier = carrier

    def clean_telephone(self):
        """Should be submitted or present in instance"""
        telephone = self.cleaned_data.get("telephone") or self.carrier.telephone
        if not telephone:
            raise forms.ValidationError("Ce champ est obligatoire.")

        return telephone

    def clean_working_area_departements(self):
        """Pads departement numbers lesser than 10 with a zero"""
        formated_departements = []
        departements = self.cleaned_data.get("working_area_departements")
        for departement in departements:
            formated_departements.append("{:0>2}".format(departement))
        # Unique and sorted
        return sorted(set(formated_departements))

    def clean_edit_code(self):
        # Access control to locked carrier
        edit_code = self.cleaned_data.get("edit_code")
        if not self.carrier.check_edit_code(edit_code):
            raise forms.ValidationError("Le code de modification n'est pas valide.")

        return edit_code

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get(
            "working_area"
        ) == WORKING_AREA_DEPARTEMENT and not cleaned_data.get(
            "working_area_departements", []
        ):
            self.add_error(
                "working_area_departements",
                "Des départements doivent être renseignés quand l'aire de travail est départementale.",
            )
