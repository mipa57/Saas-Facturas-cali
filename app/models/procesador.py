# ============================================
# Procesador de Facturas - PDF e Imágenes
# SaaS Facturas Cali
# ============================================

import pdfplumber
import base64
import os
import re
from pathlib import Path
from datetime import datetime

# ============================================
# LEER PDFs
# ============================================

def leer_pdf(ruta_pdf: str) -> str:
    """
    Extrae texto de un archivo PDF
    
    Args:
        ruta_pdf: ruta al archivo PDF
        
    Returns:
        Texto extraído del PDF
    """
    try:
        texto_completo = ""
        
        with pdfplumber.open(ruta_pdf) as pdf:
            for numero_pagina, pagina in enumerate(pdf.pages, 1):
                texto_pagina = pagina.extract_text()
                if texto_pagina:
                    texto_completo += f"\n--- Página {numero_pagina} ---\n"
                    texto_completo += texto_pagina
                    
        if not texto_completo.strip():
            print(f"⚠️ PDF sin texto extraíble: {ruta_pdf}")
            return ""
            
        print(f"✅ PDF leído: {len(texto_completo)} caracteres")
        return texto_completo
        
    except Exception as e:
        print(f"❌ Error leyendo PDF: {e}")
        raise e

# ============================================
# LEER IMÁGENES
# ============================================

def leer_imagen_base64(ruta_imagen: str) -> tuple:
    """
    Convierte imagen a base64 para enviar a Claude
    
    Args:
        ruta_imagen: ruta a la imagen
        
    Returns:
        Tupla (base64_string, media_type)
    """
    try:
        # Detectar tipo de imagen
        extension = Path(ruta_imagen).suffix.lower()
        tipos = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp"
        }
        media_type = tipos.get(extension, "image/jpeg")
        
        # Convertir a base64
        with open(ruta_imagen, "rb") as archivo:
            contenido = archivo.read()
        imagen_base64 = base64.standard_b64encode(contenido).decode("utf-8")
        
        print(f"✅ Imagen leída: {Path(ruta_imagen).name}")
        return imagen_base64, media_type
        
    except Exception as e:
        print(f"❌ Error leyendo imagen: {e}")
        raise e

# ============================================
# DETECTAR TIPO DE ARCHIVO
# ============================================

def detectar_tipo_archivo(ruta_archivo: str) -> str:
    """
    Detecta si el archivo es PDF o imagen
    
    Returns:
        'pdf', 'imagen' o 'desconocido'
    """
    extension = Path(ruta_archivo).suffix.lower()
    
    if extension == ".pdf":
        return "pdf"
    elif extension in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
        return "imagen"
    else:
        return "desconocido"

# ============================================
# VALIDAR NIT COLOMBIANO
# ============================================

def validar_nit(nit: str) -> dict:
    """
    Valida formato de NIT colombiano (XXXXXXXXX-X)
    
    Args:
        nit: NIT a validar
        
    Returns:
        Diccionario con resultado de validación
    """
    if not nit:
        return {"valido": False, "mensaje": "NIT vacío"}
    
    # Limpiar el NIT
    nit_limpio = nit.strip().replace(" ", "")
    
    # Patrón: 9 dígitos + guión + 1 dígito
    patron = r'^\d{9}-\d$'
    
    if re.match(patron, nit_limpio):
        return {
            "valido": True,
            "nit": nit_limpio,
            "mensaje": "NIT válido ✅"
        }
    else:
        return {
            "valido": False,
            "nit": nit_limpio,
            "mensaje": f"NIT inválido ❌ — formato requerido: XXXXXXXXX-X"
        }

# ============================================
# PROCESAR FACTURA COMPLETA
# ============================================

def procesar_archivo(ruta_archivo: str) -> dict:
    """
    Procesa cualquier archivo de factura (PDF o imagen)
    y retorna el contenido listo para Claude
    
    Args:
        ruta_archivo: ruta al archivo
        
    Returns:
        Diccionario con tipo y contenido del archivo
    """
    if not os.path.exists(ruta_archivo):
        raise FileNotFoundError(f"Archivo no encontrado: {ruta_archivo}")
    
    tipo = detectar_tipo_archivo(ruta_archivo)
    
    print(f"📄 Procesando: {Path(ruta_archivo).name} ({tipo})")
    
    if tipo == "pdf":
        texto = leer_pdf(ruta_archivo)
        return {
            "tipo": "pdf",
            "contenido": texto,
            "archivo": Path(ruta_archivo).name
        }
        
    elif tipo == "imagen":
        imagen_base64, media_type = leer_imagen_base64(ruta_archivo)
        return {
            "tipo": "imagen",
            "base64": imagen_base64,
            "media_type": media_type,
            "archivo": Path(ruta_archivo).name
        }
        
    else:
        raise ValueError(f"Formato no soportado: {Path(ruta_archivo).suffix}")

# ============================================
# PRUEBA
# ============================================

if __name__ == "__main__":
    print("🧪 Probando procesador de facturas...")
    
    # Prueba de validación de NIT
    nits_prueba = [
        "900123456-1",   # Válido
        "9001234561",    # Sin guión - inválido
        "90012345-1",    # Muy corto - inválido
        "900123456-12",  # Dígito verificación largo - inválido
    ]
    
    print("\n📋 Prueba de validación de NITs:")
    for nit in nits_prueba:
        resultado = validar_nit(nit)
        print(f"  {nit} → {resultado['mensaje']}")
    
    print("\n✅ Procesador listo!")
    print("   Soporta: PDF, JPG, PNG, GIF, WebP")