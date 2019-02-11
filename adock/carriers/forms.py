from django import forms

from .models import WORKING_AREA_DEPARTEMENT, Carrier


class DetailForm(forms.ModelForm):
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
        ]

    def __init__(self, data, carrier):
        super().__init__(data)
        self.carrier = carrier

    def field_required(self, field_name):
        """Should be submitted or present in instance"""
        value = self.cleaned_data.get(field_name) or getattr(self.carrier, field_name)
        if not value:
            raise forms.ValidationError("Ce champ est obligatoire.")

        return value

    def clean_telephone(self):
        return self.field_required("telephone")

    def clean_email(self):
        """Should be submitted or present in instance"""
        return self.field_required("email")

    def clean_working_area_departements(self):
        """Pads departement numbers lesser than 10 with a zero"""
        formated_departements = []
        departements = self.cleaned_data.get("working_area_departements")
        for departement in departements:
            formated_departements.append("{:0>2}".format(departement))
        # Unique and sorted
        return sorted(set(formated_departements))

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
