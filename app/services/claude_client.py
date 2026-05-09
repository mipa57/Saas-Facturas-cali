# ============================================
# Cliente de Claude API - Anthropic
# SaaS Facturas Cali
# ============================================

from anthropic import Anthropic
from dotenv import load_dotenv
import os
import json

load_dotenv()

cliente = Anthropic()
MODELO = "claude-haiku-4-5-20251001"

SYSTEM_PROMPT = """
Eres un asistente experto en facturación electrónica 
colombiana para el sistema SaaS Facturas Cali.

SIEMPRE:
- Responde en español colombiano
- Usa términos de la DIAN correctamente
- Da respuestas claras y cortas
- Menciona sanciones reales en COP cuando aplique
- Enfócate en PyMEs de Cali

NUNCA:
- Des información de otros países
- Uses términos técnicos sin explicar
- Des respuestas de más de 3 párrafos
"""

SCHEMA_FACTURA = {
    "name": "guardar_factura",
    "description": "Extrae y estructura datos de una factura colombiana",
    "input_schema": {
        "type": "object",
        "properties": {
            "nit": {
                "type": "string",
                "description": "NIT del proveedor formato XXXXXXXXX-X"
            },
            "proveedor": {
                "type": "string",
                "description": "Nombre completo del proveedor"
            },
            "fecha": {
                "type": "string",
                "description": "Fecha de la factura formato YYYY-MM-DD"
            },
            "total": {
                "type": "number",
                "description": "Total a pagar en pesos colombianos"
            },
            "numero_factura": {
                "type": "string",
                "description": "Número o consecutivo de la factura"
            },
            "items": {
                "type": "array",
                "description": "Lista de productos o servicios",
                "items": {
                    "type": "object",
                    "properties": {
                        "descripcion": {"type": "string"},
                        "valor": {"type": "number"}
                    }
                }
            }
        },
        "required": ["nit", "total", "fecha"]
    }
}

PROMPT_EXTRACCION = """
Extrae todos los datos de esta factura colombiana.

Sigue estos pasos:
1. Identifica el NIT (formato XXXXXXXXX-X)
2. Encuentra el nombre del proveedor
3. Extrae la fecha exacta
4. Calcula el total final en COP
5. Lista cada producto o servicio
"""

# ============================================
# Función básica de chat
# ============================================
def chat(mensajes: list, system_prompt: str = None, temperatura: float = 0) -> str:
    """
    Envía mensajes a Claude y retorna respuesta.

    Args:
        mensajes: lista de mensajes
        system_prompt: instrucciones del sistema
        temperatura: 0 para extracción, 0.7 para conversación
    """
    try:
        params = {
            "model": MODELO,
            "max_tokens": 2000,
            "messages": mensajes,
            "temperature": temperatura
        }
        if system_prompt:
            params["system"] = system_prompt

        respuesta = cliente.messages.create(**params)
        return respuesta.content[0].text

    except Exception as e:
        print(f"❌ Error en Claude API: {e}")
        raise e

# ============================================
# Extraer datos de factura — texto o imagen
# ============================================
def extraer_datos_factura(texto: str = None, imagen_base64: str = None, media_type: str = "image/jpeg") -> dict:
    """
    Extrae datos estructurados de una factura.
    Acepta texto (PDF) o imagen (JPG/PNG).

    Args:
        texto: texto extraído del PDF (usar si es PDF)
        imagen_base64: imagen en base64 (usar si es imagen)
        media_type: tipo MIME de la imagen ("image/jpeg", "image/png", etc.)

    Returns:
        Diccionario con datos de la factura
    """
    if texto:
        # PDF: mandar como texto plano
        contenido_usuario = [
            {
                "type": "text",
                "text": PROMPT_EXTRACCION + f"\n\nFactura:\n{texto}"
            }
        ]
    elif imagen_base64:
        # Imagen: mandar imagen real en base64
        contenido_usuario = [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": media_type,
                    "data": imagen_base64
                }
            },
            {
                "type": "text",
                "text": PROMPT_EXTRACCION
            }
        ]
    else:
        raise ValueError("Debes pasar texto= o imagen_base64=")

    try:
        respuesta = cliente.messages.create(
            model=MODELO,
            max_tokens=1000,
            temperature=0,
            tools=[SCHEMA_FACTURA],
            tool_choice={"type": "tool", "name": "guardar_factura"},
            messages=[{"role": "user", "content": contenido_usuario}]
        )

        datos = respuesta.content[0].input
        return datos

    except Exception as e:
        print(f"❌ Error extrayendo datos: {e}")
        raise e

# ============================================
# Chatbot de soporte al cliente
# ============================================
def chatbot_soporte(historial_mensajes: list, pregunta: str) -> str:
    """
    Responde preguntas del cliente sobre facturación.

    Args:
        historial_mensajes: historial de la conversación
        pregunta: nueva pregunta del cliente
    """
    historial_mensajes.append({"role": "user", "content": pregunta})

    respuesta = chat(
        mensajes=historial_mensajes,
        system_prompt=SYSTEM_PROMPT,
        temperatura=0.3
    )

    historial_mensajes.append({"role": "assistant", "content": respuesta})
    return respuesta

# ============================================
# Prueba
# ============================================
if __name__ == "__main__":
    print("🧪 Probando Claude API...")

    respuesta = chat(mensajes=[{"role": "user", "content": "Di hola en una sola línea"}])
    print(f"✅ Claude responde: {respuesta}")

    texto_prueba = """
    FERRETERÍA EL TORNILLO FELIZ
    NIT: 900123456-1
    Fecha: 01/05/2026
    Factura No: 001-2026

    Tornillos x100: $50.000
    Pintura blanca 1L: $35.000

    TOTAL: $85.000
    """

    datos = extraer_datos_factura(texto=texto_prueba)
    print(f"✅ Datos extraídos: {json.dumps(datos, indent=2, ensure_ascii=False)}")