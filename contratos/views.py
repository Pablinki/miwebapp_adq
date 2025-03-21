from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import render
from django.conf import settings
import os
import urllib.parse
import pandas as pd

from .forms import BuscarContratoForm, BuscarProveedorForm
from .utils import (
    buscar_contrato_en_excel,
    generar_documento,
    obtener_destinatarios,
    buscar_contratos_por_proveedor,
    buscar_convenios
)

# # --- Búsqueda principal por contrato/proveedor ---
# def buscar_contrato(request):
#     resultado = None
#     poliza_info = None
#     plurianual_info = None
#     convenios_resultados = []
#     contratos = []
#     destinatarios = obtener_destinatarios()

#     if request.method == "POST":
#         form = BuscarContratoForm(request.POST)
#         if form.is_valid():
#             query = form.cleaned_data["contrato"].strip()  # Entrada de usuario
#             anio = request.POST.get("anio")                # Año extra si proveedor
#             ver_convenios = request.POST.get("ver_convenios") == "on"

#             if es_formato_contrato(query):
#                 resultado = buscar_contrato_en_excel(query)

#                 if resultado:
#                     poliza_info = resultado.get("POLIZA_INFO", None)
#                     plurianual_info = resultado.get("PLURIANUAL_INFO", None)

#             else:
#                 contratos = buscar_contratos_por_proveedor(query, anio)
#                 contratos = [c for c in contratos if pd.notna(c.get("CONTRATO", None))]

#                 if ver_convenios:
#                     convenios_resultados = buscar_convenios(query, anio)

#     else:
#         form = BuscarContratoForm()

#     contexto = {
#         "form": form,
#         "resultado": resultado,
#         "contratos": contratos,
#         "convenios_resultados": convenios_resultados,
#         "destinatarios": destinatarios,
#         "poliza_info": poliza_info,
#         "plurianual_info": plurianual_info,
#     }

#     return render(request, "contratos/buscar_contrato.html", contexto)

def buscar_contrato(request):
    resultado = None
    poliza_info = None
    plurianual_info = None
    convenios_resultados = []
    contratos = []
    destinatarios = obtener_destinatarios()

    form = BuscarContratoForm()

    # --- Si es GET con contrato ---
    contrato_id = request.GET.get("contrato")
    if contrato_id:
        contrato_id = contrato_id.strip()
        print("🔍 Contrato ingresado:", contrato_id)

        # Detectamos si es contrato o proveedor
        if es_formato_contrato(contrato_id):
            resultado = buscar_contrato_en_excel(contrato_id)
            print("🔎 Resultado encontrado:", resultado)
            if resultado:
                poliza_info = resultado.get("POLIZA_INFO", None)
                plurianual_info = resultado.get("PLURIANUAL_INFO", None)

        else:
            # Es un proveedor (poco común vía GET)
            contratos = buscar_contratos_por_proveedor(contrato_id)
            contratos = [c for c in contratos if pd.notna(c.get("CONTRATO", None))]

    # --- Si es POST desde el formulario ---
    elif request.method == "POST":
        form = BuscarContratoForm(request.POST)
        if form.is_valid():
            query = form.cleaned_data["contrato"].strip()
            anio = request.POST.get("anio")
            ver_convenios = request.POST.get("ver_convenios") == "on"

            if es_formato_contrato(query):
                resultado = buscar_contrato_en_excel(query)
                if resultado:
                    poliza_info = resultado.get("POLIZA_INFO", None)
                    plurianual_info = resultado.get("PLURIANUAL_INFO", None)

            else:
                contratos = buscar_contratos_por_proveedor(query, anio)
                contratos = [c for c in contratos if pd.notna(c.get("CONTRATO", None))]

                if ver_convenios:
                    convenios_resultados = buscar_convenios(query, anio)

    # --- Contexto Final ---
    contexto = {
        "form": form,
        "resultado": resultado,
        "contratos": contratos,
        "convenios_resultados": convenios_resultados,
        "destinatarios": destinatarios,
        "poliza_info": poliza_info,
        "plurianual_info": plurianual_info,
    }

    return render(request, "contratos/buscar_contrato.html", contexto)


# --- Validación formato contrato/convenio ---
def es_formato_contrato(query):
    import re
    contrato_pattern = r'^[A-Z]+/DGRMSG/\d+/\d+/\d{4}$'
    convenio_pattern = r'^[A-Z]+/DGRMSG/\d+-[IVXLCDM]+/\d+/\d{2}$'

    return bool(re.match(contrato_pattern, query) or re.match(convenio_pattern, query))

# --- Generar documentos (poliza / firma / nuevo_documento) ---
def generar_documento_view(request):
    contrato_id = request.GET.get("contrato")
    tipo = request.GET.get("tipo")  # 'poliza', 'firma_administrador', 'garantias'
    destinatario_nombre = request.GET.get("destinatario")

    if not contrato_id or not tipo or not destinatario_nombre:
        return JsonResponse({"error": "Faltan parámetros"}, status=400)

    destinatario_nombre = urllib.parse.unquote(destinatario_nombre).strip().upper()

    resultado = buscar_contrato_en_excel(contrato_id)

    if resultado:
        destinatarios = obtener_destinatarios()
        destinatario = next((d for d in destinatarios if d["NOMBRE"].strip() == destinatario_nombre), None)

        if not destinatario:
            return JsonResponse({"error": f"Destinatario '{destinatario_nombre}' no encontrado"}, status=404)

        doc_url = generar_documento(tipo, resultado, destinatario)
        print(doc_url, "doc_url... desde generar_documento_view")

        if doc_url:
            return JsonResponse({"success": True, "doc_url": doc_url})
        else:
            return JsonResponse({"error": "No se pudo generar el documento"}, status=500)

    return JsonResponse({"error": "Contrato no encontrado"}, status=404)

# --- Mostrar documentos generados ---
def listar_documentos(request):
    ruta_docs = settings.MEDIA_ROOT
    archivos = os.listdir(ruta_docs)
    return JsonResponse({"archivos": archivos})

# --- Servir archivos media ---
def servir_archivo_media(request, path):
    file_path = os.path.join(settings.MEDIA_ROOT, path)

    if os.path.exists(file_path):
        return FileResponse(open(file_path, "rb"), as_attachment=True)
    else:
        raise Http404("Archivo no encontrado")

# --- Buscar contratos por proveedor clásico ---
def buscar_por_proveedor(request):
    resultados = None

    if request.method == "POST":
        form = BuscarProveedorForm(request.POST)
        if form.is_valid():
            proveedor = form.cleaned_data["proveedor"]
            resultados = buscar_contratos_por_proveedor(proveedor)

    else:
        form = BuscarProveedorForm()

    contexto = {
        "form": form,
        "resultados": resultados,
    }

    return render(request, "contratos/resultados_proveedor.html", contexto)
