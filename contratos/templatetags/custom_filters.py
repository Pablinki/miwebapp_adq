from datetime import datetime
from django import template
import re
register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, "")

MESES_ES = {
    "January": "enero", "February": "febrero", "March": "marzo", "April": "abril",
    "May": "mayo", "June": "junio", "July": "julio", "August": "agosto",
    "September": "septiembre", "October": "octubre", "November": "noviembre", "December": "diciembre"
}

@register.filter
def quitar_hora(valor):
    if isinstance(valor, datetime):
        dia = valor.day
        mes_en = valor.strftime("%B")
        mes_es = MESES_ES.get(mes_en, mes_en)
        año = valor.year
        return f"{dia} de {mes_es} de {año}"
    elif valor is not None:
        valor = str(valor)
        valor = re.sub(r'\s+a las\s+\d{2}:\d{2}', '', valor)
    return valor