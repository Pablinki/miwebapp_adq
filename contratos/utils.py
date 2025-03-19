import pandas as pd
from docx import Document
import os
from django.conf import settings
from datetime import datetime
import re
from rapidfuzz import process, fuzz

ruta_excel = settings.EXCEL_FILE_PATH
ruta_docs = settings.MEDIA_PATH

MESES_ES = {
    "January": "enero", "February": "febrero", "March": "marzo", "April": "abril",
    "May": "mayo", "June": "junio", "July": "julio", "August": "agosto",
    "September": "septiembre", "October": "octubre", "November": "noviembre", "December": "diciembre"
}

# ✅ FORMATO DE FECHAS Y MONEDAS
def formatear_fecha(fecha):
    if pd.isna(fecha) or fecha == "":
        return "N/A"
    try:
        fecha_obj = pd.to_datetime(fecha)
        dia = fecha_obj.day
        mes = MESES_ES[fecha_obj.strftime("%B")]
        año = fecha_obj.strftime("%y")
        return f"{dia:02d}-{mes}-{año}"
    except Exception:
        return "N/A"

def obtener_fecha_hoy():
    hoy = datetime.today()
    dia = hoy.day
    mes = MESES_ES[hoy.strftime("%B")]
    año = hoy.year
    return f"Ciudad de México, {dia} de {mes} de {año}"

def formatear_moneda(valor):
    try:
        return f"${float(valor):,.2f}" if valor not in ["", "N/A"] else "N/A"
    except ValueError:
        return "N/A"

# ✅ LIMPIEZA DE NOMBRES Y RFC
def limpiar_nombre_proveedor(nombre):
    if not isinstance(nombre, str):
        return nombre
    nombre = re.sub(r'\b(S\.?A\.? DE C\.?V\.?|S\.? DE R\.?L\.?|S\.?C\.?|SAPI DE C\.?V\.?)\b', '', nombre, flags=re.IGNORECASE)
    return " ".join(nombre.split()).strip()

def corregir_nombre_proveedor(nombre, lista_proveedores):
    mejor_coincidencia, puntuacion, _ = process.extractOne(nombre, lista_proveedores, scorer=fuzz.token_sort_ratio)
    return mejor_coincidencia if puntuacion >= 80 else nombre

def buscar_rfc(nombre_proveedor, df_rfc):
    if "PROVEEDOR" in df_rfc.columns:
        df_rfc["PROVEEDOR"] = df_rfc["PROVEEDOR"].map(lambda x: limpiar_nombre_proveedor(x) if isinstance(x, str) else x)
        lista_proveedores = df_rfc["PROVEEDOR"].dropna().unique().tolist()
        nombre_proveedor_limpio = limpiar_nombre_proveedor(nombre_proveedor)
        nombre_proveedor_corregido = corregir_nombre_proveedor(nombre_proveedor_limpio, lista_proveedores)
        rfc_resultado = df_rfc[df_rfc["PROVEEDOR"].str.lower() == nombre_proveedor_corregido.lower()]
        return rfc_resultado.iloc[0]["RFC"] if not rfc_resultado.empty else "N/A"
    return "Error en datos"

# ✅ DESTINATARIOS
def obtener_destinatarios():
    try:
        df = pd.read_excel(ruta_excel, sheet_name="Destinatarios").fillna("")
        for d in df.to_dict(orient="records"):
            d["NOMBRE"] = d["NOMBRE"].strip().replace("\u00A0", " ")
        return df.to_dict(orient="records")
    except Exception:
        return []

# ✅ BÚSQUEDAS
def buscar_contrato_en_excel(contrato_id):
    año_contrato = extraer_año_contrato(contrato_id)
    if not año_contrato:
        return None

    try:
        hojas_excel = pd.ExcelFile(ruta_excel).sheet_names
        if año_contrato not in hojas_excel:
            return None

        df = pd.read_excel(ruta_excel, sheet_name=año_contrato).fillna("")
        resultado = df[df["CONTRATO"] == contrato_id]

        if resultado.empty:
            return None

        row = resultado.iloc[0]
        resultado_dict = row.to_dict()

        resultado_dict.update({
            "IMPORTE_MAX_SIN_IVA": formatear_moneda(row.get("IMPORTE MAXIMO (SIN IVA)")),
            "IVA": formatear_moneda(row.get("IVA")),
            "TOTAL_MAX": formatear_moneda(row.get("TOTAL MAXIMO")),
            "IMPORTE_MIN_SIN_IVA": formatear_moneda(row.get("IMPORTE MÍNIMO (SIN IVA)")),
            "IVA2": formatear_moneda(row.get("IVA2")),
            "TOTAL_MIN": formatear_moneda(row.get("TOTAL MINIMO")),
            "FECHA_INICIO": formatear_fecha(row.get("INICIO DE VIGENCIA")),
            "FECHA_FIN": formatear_fecha(row.get("FIN DE VIGENCIA")),
            "OBSERVACIONES": row.get("OBSERVACIONES", "N/A"),
        })

        total_maximo = float(row.get("TOTAL MAXIMO", 0)) or 0
        resultado_dict.update({
            "FIANZA_DE_CUMPLIMIENTO": calcular_monto(row.get("FIANZA DE CUMPLIMIENTO"), total_maximo),
            "POLIZA_DE_RESPONSABILIDAD_CIVIL": calcular_monto(row.get("POLIZA DE RESPONSABILIDAD CIVIL"), total_maximo),
            "VICIOS_OCULTOS": calcular_monto(row.get("VICIOS OCULTOS"), total_maximo),
            "FIANZA_DE_ANTICIPO": calcular_monto(row.get("FIANZA DE ANTICIPO"), total_maximo),
            "REPSE": calcular_monto(row.get("REPSE"), total_maximo)
        })

        try:
            df_rfc = pd.read_excel(ruta_excel, sheet_name="RFC")
            resultado_dict["RFC"] = buscar_rfc(resultado_dict["PROVEEDOR"], df_rfc)
        except Exception:
            resultado_dict["RFC"] = "Error RFC"

        if resultado_dict.get("PLURI", "").strip().upper() == "SI":
            try:
                df_pluri = pd.read_excel(ruta_excel, sheet_name="Plurianuales").fillna("")
                pluri_resultado = df_pluri[df_pluri["CONTRATO"] == contrato_id]
                if not pluri_resultado.empty:
                    resultado_dict["PLURIANUAL_INFO"] = pluri_resultado.iloc[0].to_dict()
            except Exception:
                pass

        return resultado_dict
    except Exception:
        return None

def buscar_contratos_por_proveedor(proveedor, anio=None):
    contratos = []
    xl = pd.ExcelFile(ruta_excel)

    for sheet_name in xl.sheet_names:
        df = xl.parse(sheet_name).fillna("")
        df_filtrado = df[df["PROVEEDOR"].str.contains(proveedor, case=False, na=False)]
        if anio:
            df_filtrado = df_filtrado[df_filtrado["CONTRATO"].str.contains(f"/{anio}")]
        for _, row in df_filtrado.iterrows():
            contratos.append({
                "CONTRATO": row["CONTRATO"],
                "PROVEEDOR": row["PROVEEDOR"],
                "DESCRIPCIÓN": row.get("DESCRIPCIÓN", "N/A")
            })

    return contratos

def buscar_convenios(proveedor, anio=None):
    convenios = []
    xl = pd.ExcelFile(ruta_excel)

    for sheet_name in xl.sheet_names:
        df = xl.parse(sheet_name).fillna("")
        df_filtrado = df[
            (df["PROVEEDOR"].str.contains(proveedor, case=False, na=False)) &
            (df["CONTRATO"].str.contains(r'-[IVXLCDM]+/', na=False))
        ]
        if anio:
            df_filtrado = df_filtrado[df_filtrado["CONTRATO"].str.endswith(f"/{str(anio)[-2:]}")]
        for _, row in df_filtrado.iterrows():
            convenios.append({
                "CONTRATO": row["CONTRATO"],
                "PROVEEDOR": row["PROVEEDOR"],
                "DESCRIPCIÓN": row.get("DESCRIPCIÓN", "N/A")
            })

    return convenios

def extraer_año_contrato(contrato_id):
    partes = contrato_id.split("/")
    for parte in partes:
        if parte.isdigit() and parte in ["2020", "2021", "2022", "2023", "2024", "2025"]:
            return parte
    return None

def calcular_monto(valor, total_maximo):
    try:
        if pd.isna(valor) or valor == "" or total_maximo == 0:
            return "NO APLICA"
        if isinstance(valor, str) and "%" in valor:
            valor = valor.replace("%", "").strip()
        monto = (float(valor)) * float(total_maximo)
        return f"${monto:,.2f}"
    except Exception:
        return "NO APLICA"

# ✅ GENERAR DOCUMENTOS
def generar_documento(tipo, datos_contrato, destinatario):
    output_dir = os.path.join(settings.MEDIA_ROOT, "DocsGenerados")
    os.makedirs(output_dir, exist_ok=True)

    plantilla_path = os.path.join(settings.BASE_DIR, "contratos/doc_templates", f"{tipo}.docx")
    output_filename = f"{tipo}_{datos_contrato['CONTRATO'].replace('/', '_')}.docx"
    output_path = os.path.join(output_dir, output_filename)

    if not os.path.exists(plantilla_path):
        print(f" Plantilla no encontrada: {plantilla_path}")
        return None

    doc = Document(plantilla_path)
    fecha_hoy = obtener_fecha_hoy()

    reemplazos = {
        "{CONTRATO}": datos_contrato.get("CONTRATO", "N/A"),
        "{PROVEEDOR}": datos_contrato.get("PROVEEDOR", "N/A"),
        "{DESCRIPCION}": datos_contrato.get("DESCRIPCIÓN", "N/A"),
        "{FECHA_HOY}": fecha_hoy,
        "{NOMBRE}": destinatario.get("NOMBRE", "N/A"),
        "{CARGO}": destinatario.get("CARGO", "N/A"),
    }

    if tipo == "poliza":
        reemplazos["{INICIO_VIGENCIA}"] = datos_contrato.get("FECHA_INICIO", "N/A")
        reemplazos["{FIN_VIGENCIA}"] = datos_contrato.get("FECHA_FIN", "N/A")

    if tipo == "nuevo_documento":
        reemplazos["{EXTRA_CAMPO}"] = datos_contrato.get("EXTRA_CAMPO", "N/A")

    for p in doc.paragraphs:
        for key, value in reemplazos.items():
            p.text = p.text.replace(key, str(value))

    doc.save(output_path)
    return f"{settings.MEDIA_URL}DocsGenerados/{output_filename}"
