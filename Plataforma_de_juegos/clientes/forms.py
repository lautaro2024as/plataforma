from django import forms

from administrador.models import PerfilUsuario


class PerfilUsuarioForm(forms.ModelForm):
    class Meta:
        model = PerfilUsuario
        fields = ("telefono", "direccion", "ciudad", "fecha_nacimiento")
        widgets = {
            "telefono": forms.TextInput(attrs={"autocomplete": "tel"}),
            "direccion": forms.TextInput(attrs={"autocomplete": "street-address"}),
            "ciudad": forms.TextInput(attrs={"autocomplete": "address-level2"}),
            "fecha_nacimiento": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }
