import pandas as pd
from docx import Document
import os
from django.conf import settings
from datetime import datetime
import re
from rapidfuzz import process, fuzz

EXCEL_FILE_PATH = "C:\\Users\\juan.franco\\miwebapp\\excel_reader\\BASE CONTRATOS - 2025.01.23.xlsx"

# Ruta de la carpeta donde se generarán los documentos
MEDIA_PATH = os.path.join(settings.MEDIA_ROOT, "DocsGenerados")



# Diccionario para traducir nombres de meses al español
MESES_ES = {
    "January": "enero", "February": "febrero", "March": "marzo", "April": "abril",
    "May": "mayo", "June": "junio", "July": "julio", "August": "agosto",
    "September": "septiembre", "October": "octubre", "November": "noviembre", "December": "diciembre"
}


def formatear_fecha(fecha):
    """Convierte una fecha en formato '01-ene-25' utilizando el diccionario de meses en español."""
    if pd.isna(fecha) or fecha == "":
        return "N/A"

    try:
        fecha_obj = pd.to_datetime(fecha)  # Convertir a objeto datetime
        dia = fecha_obj.day
        mes = MESES_ES[fecha_obj.strftime("%B")]  # Traducir el mes completo
        año = fecha_obj.strftime("%y")  # Obtener los últimos 2 dígitos del año
        return f"{dia:02d}-{mes}-{año}"
    except Exception as e:
        print(f"Error al formatear fecha: {e}")
        return "N/A"


def obtener_fecha_hoy():
    """Devuelve la fecha actual en el formato: Ciudad de México, 27 de diciembre de 2024"""
    hoy = datetime.today()
    dia = hoy.day
    mes = MESES_ES[hoy.strftime("%B")]  # Traducir el mes al español
    año = hoy.year
    return f"Ciudad de México, {dia} de {mes} de {año}"

def obtener_destinatarios():
    """Lee la hoja 'Destinatarios' del Excel y devuelve una lista de destinatarios."""
    try:
        df = pd.read_excel(EXCEL_FILE_PATH, sheet_name="Destinatarios")
        df = df.fillna("")  # Rellenar valores nulos con cadenas vacías
        destinatarios = df.to_dict(orient="records")  # Convertir a lista de diccionarios
        
        #  Limpiar nombres eliminando espacios extras y caracteres no imprimibles
        for d in destinatarios:
            d["NOMBRE"] = d["NOMBRE"].strip().replace("\u00A0", " ")

        
        return destinatarios

    except Exception as e:
        print(f"Error al leer la hoja 'Destinatarios': {e}")
        return []


# Lista de terminaciones a eliminar
#PATTERN_EMPRESAS = r",?\s*S\.A\. DE C\.V\.|,?\s*S\.A\.|,?\s*S\. DE R\.L\. DE C\.V\.|,?\s*S\.C\.|,?\s*S\.P\.R\. DE R\.L\."

def limpiar_nombre_proveedor(nombre):
    """Elimina terminaciones como 'S.A. de C.V.', 'S. de R.L.', etc. del nombre del proveedor."""
    if not isinstance(nombre, str):
        return nombre

    # Eliminar sufijos comerciales comunes en México
    nombre = re.sub(r'\b(S\.?A\.? DE C\.?V\.?|S\.? DE R\.?L\.?|S\.?C\.?|SAPI DE C\.?V\.?)\b', '', nombre, flags=re.IGNORECASE)
    
    # Eliminar espacios en exceso
    nombre = " ".join(nombre.split()).strip()

    return nombre





def corregir_nombre_proveedor(nombre, lista_proveedores):
    """Corrige errores tipográficos en nombres de proveedores usando coincidencia aproximada."""
    mejor_coincidencia, puntuacion, _ = process.extractOne(nombre, lista_proveedores, scorer=fuzz.token_sort_ratio)
   
    # Si la coincidencia es mayor al 80%, corregimos el nombre
    if puntuacion >= 80:
        print(f"✅ Nombre corregido: '{nombre}' ➜ '{mejor_coincidencia}' ({puntuacion}% de coincidencia)")
        return mejor_coincidencia
    else:
        print(f"⚠️ No se encontró una coincidencia cercana para '{nombre}', usando nombre original.")
        return nombre


def buscar_rfc(nombre_proveedor, df_rfc):
    """Busca el RFC de un proveedor en la hoja 'RFC', aplicando corrección de errores tipográficos."""

    if "PROVEEDOR" in df_rfc.columns:
        # Limpiar nombres de proveedores en el DataFrame
        df_rfc["PROVEEDOR"] = df_rfc["PROVEEDOR"].map(lambda x: limpiar_nombre_proveedor(x) if isinstance(x, str) else x)

        # Obtener la lista de proveedores limpios
        lista_proveedores = df_rfc["PROVEEDOR"].dropna().unique().tolist()
        #print(lista_proveedores,"lista de proveedores")
        # Limpiar y corregir el nombre ingresado
        nombre_proveedor_limpio = limpiar_nombre_proveedor(nombre_proveedor)
        
        nombre_proveedor_corregido = corregir_nombre_proveedor(nombre_proveedor_limpio, lista_proveedores)
        
        print(f"🔍 Buscando RFC para: '{nombre_proveedor_corregido}'")

        # Buscar el RFC con el nombre corregido
        rfc_resultado = df_rfc[df_rfc["PROVEEDOR"].str.lower() == nombre_proveedor_corregido.lower()]

        if not rfc_resultado.empty:
            return rfc_resultado.iloc[0]["RFC"]
        else:
            return "N/A"  # Si no se encuentra, asigna "N/A"
    else:
        print("⚠️ Error: La hoja 'RFC' no tiene la columna 'PROVEEDOR'.")
        return "Error en datos"


# Ruta del archivo Excel con la información
#EXCEL_FILE = "C:\\Users\\juan.franco\\Downloads\\BASE_CONTRATOS.xlsx"

def formatear_moneda(valor):
    """Convierte un número en formato de moneda ($1,000.00)."""
    try:
        return f"${float(valor):,.2f}" if valor not in ["", "N/A"] else "N/A"
    except ValueError:
        return "N/A"


HOJAS_DISPONIBLES = ["2020", "2021", "2022", "2023", "2024", "2025", "Plurianuales"]

def extraer_año_contrato(contrato_id):
    """Extrae el año del contrato desde la cadena del contrato."""
    partes = contrato_id.split("/")  # Divide el contrato en partes
    for parte in partes:
        if parte.isdigit() and parte in HOJAS_DISPONIBLES:  # Si es un año válido
            return parte
    return None  # Si no encuentra el año, retorna Non

def calcular_monto(valor, total_maximo):
    """Calcula el monto en dinero basado en el porcentaje de la columna y el TOTAL MÁXIMO."""
    try:
        
        if pd.isna(valor) or valor == "" or total_maximo == 0 or pd.isna(total_maximo):
            return "NO APLICA"
        
        # Si el valor contiene "%", eliminarlo y convertirlo a número
        if isinstance(valor, str) and "%" in valor:
           valor = valor.replace("%", "").strip()
           
        monto = (float(valor) ) * float(total_maximo)  # Calcular el monto
        return f"${monto:,.2f}"  # Formato de moneda con separadores
    except Exception:
        return "NO APLICA"


def buscar_contrato_en_excel(contrato_id):
    """Busca un contrato en el archivo Excel verificando el año correcto."""
    año_contrato = extraer_año_contrato(contrato_id)  # Extraer el año correcto

    if not año_contrato:
        print(f"⚠ Error: No se encontró un año válido en el contrato: {contrato_id}")
        return None


    try:
        
        # Verificar si la hoja existe antes de abrirla
        hojas_excel = pd.ExcelFile(EXCEL_FILE_PATH).sheet_names
        if año_contrato not in hojas_excel:
            print(f"⚠ Error: La hoja '{año_contrato}' no existe en el archivo Excel.")
            return None
        
        # Leer la hoja correspondiente al año del contrato
        df = pd.read_excel(EXCEL_FILE_PATH, sheet_name=año_contrato)
        df = df.fillna("")  # Reemplazar valores nulos con cadenas vacías

        resultado = df[df["CONTRATO"] == contrato_id]

        if not resultado.empty:
            resultado_dict = resultado.to_dict(orient="records")[0]
            
            resultado_dict["IMPORTE_MAX_SIN_IVA"] = formatear_moneda(resultado.iloc[0].get("IMPORTE MAXIMO (SIN IVA)", "N/A"))
            resultado_dict["IVA"] = formatear_moneda(resultado.iloc[0].get("IVA", "N/A"))
            resultado_dict["TOTAL_MAX"] = formatear_moneda(resultado.iloc[0].get("TOTAL MAXIMO", "N/A"))
            resultado_dict["IMPORTE_MIN_SIN_IVA"] = formatear_moneda(resultado.iloc[0].get("IMPORTE MÍNIMO (SIN IVA)", "N/A"))
            resultado_dict["IVA2"] = formatear_moneda(resultado.iloc[0].get("IVA2", "N/A"))
            resultado_dict["TOTAL_MIN"] = formatear_moneda(resultado.iloc[0].get("TOTAL MINIMO", "N/A"))
            resultado_dict["FECHA_INICIO"] = formatear_fecha(resultado.iloc[0].get("INICIO DE VIGENCIA", "N/A"))
            resultado_dict["FECHA_FIN"] = formatear_fecha(resultado.iloc[0].get("FIN DE VIGENCIA", "N/A"))
            resultado_dict["OBSERVACIONES"] = resultado.iloc[0].get("OBSERVACIONES", "N/A")
            
            # Obtener el TOTAL MÁXIMO para calcular montos
            total_maximo = resultado_dict.get("TOTAL MAXIMO", 0)

            # Calcular montos en dinero o asignar "NO APLICA"
            resultado_dict["FIANZA_DE_CUMPLIMIENTO"] = calcular_monto(resultado_dict.get("FIANZA DE CUMPLIMIENTO", ""), total_maximo)
            resultado_dict["POLIZA_DE_RESPONSABILIDAD_CIVIL"] = calcular_monto(resultado_dict.get("POLIZA DE RESPONSABILIDAD CIVIL", ""), total_maximo)
            resultado_dict["VICIOS_OCULTOS"] = calcular_monto(resultado_dict.get("VICIOS OCULTOS", ""), total_maximo)
            resultado_dict["FIANZA_DE_ANTICIPO"] = calcular_monto(resultado_dict.get("FIANZA DE ANTICIPO", ""), total_maximo)
            resultado_dict["REPSE"] = calcular_monto(resultado_dict.get("REPSE", ""), total_maximo)

            # Extraer información del RFC desde la hoja "RFC"
              
            try:
               df_rfc = pd.read_excel(EXCEL_FILE_PATH, sheet_name="RFC")
               
               
               if not df_rfc.empty:
                   resultado_dict["RFC"] = buscar_rfc(resultado_dict["PROVEEDOR"], df_rfc)
                   
               else:
                   resultado_dict["RFC"] = "Error en datos RFC al buscar en dict proveedor"

            except Exception as e:
                print(f"Error al leer la hoja 'RFC desde la funcion buscar_contratos_excel': {e}")
                resultado_dict["RFC"] = "Error de datos RFC"               

            # Verificar si el contrato es plurianual y extraer datos de la hoja "Plurianuales"
            if resultado_dict.get("PLURI", "").strip().upper() == "SI":
                try:
                    df_pluri = pd.read_excel(EXCEL_FILE_PATH, sheet_name="Plurianuales")
                    df_pluri = df_pluri.fillna("")
                    pluri_resultado = df_pluri[df_pluri["CONTRATO"] == contrato_id]

                    if not pluri_resultado.empty:
                        resultado_dict["PLURIANUAL_INFO"] = pluri_resultado.to_dict(orient="records")[0]
                except Exception as e:
                    print(f"Error al leer hoja 'Plurianuales': {e}")

            return resultado_dict  # Retornar el contrato encontrado

    except Exception as e:
        print(f"Error al leer el archivo Excel: {e}")

    return None  # Si no se encuentra el contrato
        

def generar_documento(tipo, datos_contrato, destinatario):
    
    output_dir = settings.MEDIA_ROOT / "DocsGenerados"
    os.makedirs(output_dir, exist_ok=True)  # ✅ Asegurar que la carpeta existe
    
    """Genera un documento Word con datos comunes y específicos según el tipo de documento"""
    plantilla_path = os.path.join(settings.BASE_DIR, "contratos", "doc_templates", f"{tipo}.docx")
    output_filename = f"{tipo}_{datos_contrato['CONTRATO'].replace('/', '_')}.docx"
    output_path = os.path.join(MEDIA_PATH, output_filename)
    
    if not os.path.exists(plantilla_path):
        return None

    doc = Document(plantilla_path)
    fecha_hoy = obtener_fecha_hoy()

    # Diccionario de reemplazos comunes
    reemplazos = {
        "{CONTRATO}": datos_contrato["CONTRATO"],
        "{PROVEEDOR}": datos_contrato["PROVEEDOR"],
        "{DESCRIPCION}": datos_contrato["DESCRIPCIÓN"],
        "{FECHA_HOY}": fecha_hoy,
        "{NOMBRE}": destinatario["NOMBRE"],
        "{CARGO}": destinatario["CARGO"]
    }

    # Agregar reemplazos específicos por tipo de documento
    if tipo == "poliza":
        reemplazos["{INICIO_VIGENCIA}"] = datos_contrato.get("INICIO DE VIGENCIA", "N/A")
        reemplazos["{FIN_VIGENCIA}"] = datos_contrato.get("FIN DE VIGENCIA", "N/A")

    # Reemplazar en el documento
    for p in doc.paragraphs:
        for key, value in reemplazos.items():
            p.text = p.text.replace(key, str(value))

    doc.save(output_path)

    # Devolver la URL del documento para descargar
    #return f"DocsGenerados/{output_filename}"
    return f"media/DocsGenerados/{output_filename}"


def buscar_contratos_por_proveedor(proveedor):
    """Busca contratos en el Excel filtrando por proveedor con coincidencia parcial."""
    
    xl = pd.ExcelFile(EXCEL_FILE_PATH)
    contratos = []

    for sheet_name in xl.sheet_names:
        df = xl.parse(sheet_name)

        if "PROVEEDOR" in df.columns and "CONTRATO" in df.columns:
            # Filtrar por coincidencia parcial
            df_filtrado = df[df["PROVEEDOR"].str.contains(proveedor, case=False, na=False, regex=True)]

            for _, row in df_filtrado.iterrows():
                contratos.append({
                    "contrato": row["CONTRATO"],
                    "proveedor": row["PROVEEDOR"],
                    "descripcion": row.get("DESCRIPCIÓN", "N/A"),
                })

    return contratos if contratos else None
