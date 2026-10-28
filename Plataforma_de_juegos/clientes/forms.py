import re

from django import forms
from django.core.exceptions import ValidationError

from administrador.models import PerfilUsuario


class PerfilUsuarioForm(forms.ModelForm):
    def clean_telefono(self):
        telefono = self.cleaned_data.get("telefono", "").strip()
        if telefono and not re.fullmatch(r"\+?[0-9()\-\s]{7,30}", telefono):
            raise ValidationError("Ingresá un teléfono válido (7 a 30 caracteres; números, espacios y +()-).")
        return telefono

    class Meta:
        model = PerfilUsuario
        fields = ("telefono", "direccion", "ciudad", "fecha_nacimiento")
        widgets = {
            "telefono": forms.TextInput(attrs={"autocomplete": "tel"}),
            "direccion": forms.TextInput(attrs={"autocomplete": "street-address"}),
            "ciudad": forms.TextInput(attrs={"autocomplete": "address-level2"}),
            "fecha_nacimiento": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }
