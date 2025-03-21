from django import forms

class BuscarContratoForm(forms.Form):
    contrato = forms.CharField(label="Número de Contrato",
                               max_length=255,widget=forms.TextInput(attrs={"size": 30}))

class BuscarProveedorForm(forms.Form):
    proveedor = forms.CharField(
        label="Empresa / Proveedor",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"size":30,"id": "id_contrato"}))