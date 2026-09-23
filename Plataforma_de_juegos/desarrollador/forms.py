from django import forms

from administrador.models import Juego


class PublicarJuegoForm(forms.ModelForm):
    class Meta:
        model = Juego
        fields = [
            "titulo",
            "categoria",
            "precio",
            "precio_original",
            "imagen_url",
            "descripcion",
            "calificacion",
            "tipo_clave",
            "etiqueta_mas_18",
            "archivo_exe",
        ]
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 4}),
        }


class PrecioJuegoForm(forms.ModelForm):
    class Meta:
        model = Juego
        fields = ["precio"]
