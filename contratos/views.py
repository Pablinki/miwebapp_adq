from django.http import FileResponse, Http404
from django.shortcuts import render
#from urllib.parse import unquote
from django.http import JsonResponse
from django.conf import settings
import os
import urllib.parse  # Importar para decodificar la URL
from .forms import BuscarContratoForm, BuscarProveedorForm
from .utils import buscar_contrato_en_excel, generar_documento, obtener_destinatarios, buscar_contratos_por_proveedor

def buscar_contrato(request):
    resultado = None
    poliza_info = None
    plurianual_info = None
    destinatarios = obtener_destinatarios()  # Obtener destinatarios desde el Excel
    #contratos_multiples = None  # Para manejar múltiples contratos por proveedor
    
    if request.method == "POST":
        form = BuscarContratoForm(request.POST)
        if form.is_valid():
            contrato_id = form.cleaned_data["contrato"]
            #proveedor = form.cleaned_data.get("proveedor", "").strip()
            resultado = buscar_contrato_en_excel(contrato_id)
            
            if resultado:
                poliza_info = resultado.get("POLIZA_INFO", None)
                plurianual_info = resultado.get("PLURIANUAL_INFO", None)
                    
           # Debug: Verificar si se está obteniendo el RFC
           #print("🔍 RFC encontrado:", resultado.get("RFC", "No encontrado") if resultado else "No encontrado")
            

    else:
        form = BuscarContratoForm()
    
    contexto = {
        "form": form,
        "resultado": resultado,
        #"contratos_multiples": contratos_multiples,  # Lista de contratos si hay varios
        "destinatarios": destinatarios,
        "poliza_info": poliza_info,
        "plurianual_info": plurianual_info,
        #"MEDIA_URL": settings.MEDIA_URL,  # Asegurar que MEDIA_URL esté disponible en la plantilla
    }

    return render(request, "contratos/buscar_contrato.html", contexto)

def generar_documento_view(request):
    """Vista para generar el documento seleccionado con los datos del contrato y destinatario."""
    contrato_id = request.GET.get("contrato")
    tipo = request.GET.get("tipo")  # 'poliza' o 'firma_administrador'
    destinatario_nombre = request.GET.get("destinatario")

    if not contrato_id or not tipo or not destinatario_nombre:
        return JsonResponse({"error": "Faltan parámetros"}, status=400)
    
    # Decodificar el nombre del destinatario desde la URL y normalizarlo
    destinatario_nombre = urllib.parse.unquote(destinatario_nombre).strip().upper()

    resultado = buscar_contrato_en_excel(contrato_id)

    if resultado:
        destinatarios = obtener_destinatarios()
        #  LIMPIAR espacios y caracteres especiales del nombre recibido
        destinatario_nombre = destinatario_nombre.strip().replace("\u00A0", " ")  # Eliminar espacios no rompibles

        #  Comparar nombres eliminando espacios extra
        destinatario = next((d for d in destinatarios if d["NOMBRE"].strip() == destinatario_nombre), None)
        
        if not destinatario:
            return JsonResponse({"error": f"Destinatario '{destinatario_nombre}' no encontrado"}, status=404)

        #doc_path = generar_documento(tipo, resultado, destinatario)
        doc_url = generar_documento(tipo, resultado, destinatario)
        print(doc_url, "doc_url... desde generar_documento_view")
        
        if doc_url:
            return JsonResponse({"success": True, "doc_url": doc_url})
        else:
            return JsonResponse({"error": "No se pudo generar el documento"}, status=500)

        # if doc_path:
        #     return JsonResponse({"success": True, "doc_url": f"C:\\Users\\juan.franco\\miwebapp\\contratos\\DocsGenerados\\{os.path.basename(doc_path)}"})
        # else:
        #     return JsonResponse({"error": "No se pudo generar el documento"}, status=500)

    return JsonResponse({"error": "Contrato no encontrado"}, status=404)


def listar_documentos(request):
    """Muestra los documentos generados en DocsGenerados."""
    ruta_docs = settings.MEDIA_ROOT  # Ruta a DocsGenerados
    archivos = os.listdir(ruta_docs)  # Lista de archivos

    return JsonResponse({"archivos": archivos})

def servir_archivo_media(request, path):
    """Vista para servir archivos desde `MEDIA_ROOT` cuando `DEBUG=False`."""
    file_path = os.path.join(settings.MEDIA_ROOT, path)

    if os.path.exists(file_path):
        return FileResponse(open(file_path, "rb"), as_attachment=True)
    else:
        raise Http404("Archivo no encontrado")

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
        #"MEDIA_URL": settings.MEDIA_URL,
    }

    return render(request, "contratos/resultados_proveedor.html", contexto)