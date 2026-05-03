# ============================================
# Cliente de Claude API - Anthropic
# SaaS Facturas Cali
# ============================================

from anthropic import Anthropic
from dotenv import load_dotenv
import os
import json

# Cargar variables de entorno
load_dotenv()

# Inicializar cliente
cliente = Anthropic()
MODELO = "claude-haiku-4-5-20251001"

# System prompt del SaaS
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

# ============================================
# Función básica de chat
# ============================================
def chat(mensajes: list, system_prompt: str = None, temperatura: float = 0) -> str:
    """
    Envía mensajes a Claude y retorna respuesta
    
    Args:
        mensajes: lista de mensajes
        system_prompt: instrucciones del sistema
        temperatura: 0 para extracción, 0.7 para conversación
        
    Returns:
        Texto de la respuesta
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
# Extraer datos de factura con Tool Use
# ============================================
def extraer_datos_factura(texto_factura: str) -> dict:
    """
    Extrae datos estructurados de una factura usando Claude
    
    Args:
        texto_factura: texto extraído del PDF o imagen
        
    Returns:
        Diccionario con datos de la factura
    """
    
    schema_factura = {
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
    
    try:
        respuesta = cliente.messages.create(
            model=MODELO,
            max_tokens=1000,
            temperature=0,  # Siempre 0 para extracción
            tools=[schema_factura],
            tool_choice={"type": "tool", "name": "guardar_factura"},
            messages=[
                {
                    "role": "user",
                    "content": f"""
                    Extrae todos los datos de esta factura colombiana.
                    
                    Sigue estos pasos:
                    1. Identifica el NIT (formato XXXXXXXXX-X)
                    2. Encuentra el nombre del proveedor
                    3. Extrae la fecha exacta
                    4. Calcula el total final en COP
                    5. Lista cada producto o servicio
                    
                    Factura:
                    {texto_factura}
                    """
                }
            ]
        )
        
        # Extraer datos del tool use
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
    Responde preguntas del cliente sobre facturación
    
    Args:
        historial_mensajes: historial de la conversación
        pregunta: nueva pregunta del cliente
        
    Returns:
        Respuesta de Claude
    """
    # Agregar nueva pregunta
    historial_mensajes.append({
        "role": "user",
        "content": pregunta
    })
    
    respuesta = chat(
        mensajes=historial_mensajes,
        system_prompt=SYSTEM_PROMPT,
        temperatura=0.3  # Un poco de variación para conversación
    )
    
    # Guardar respuesta en historial
    historial_mensajes.append({
        "role": "assistant",
        "content": respuesta
    })
    
    return respuesta

# ============================================
# Prueba
# ============================================
if __name__ == "__main__":
    print("🧪 Probando Claude API...")
    
    # Prueba básica
    respuesta = chat(
        mensajes=[{"role": "user", "content": "Di hola en una sola línea"}]
    )
    print(f"✅ Claude responde: {respuesta}")
    
    # Prueba extracción
    texto_prueba = """
    FERRETERÍA EL TORNILLO FELIZ
    NIT: 900123456-1
    Fecha: 01/05/2026
    Factura No: 001-2026
    
    Tornillos x100: $50.000
    Pintura blanca 1L: $35.000
    
    TOTAL: $85.000
    """
    
    datos = extraer_datos_factura(texto_prueba)
    print(f"✅ Datos extraídos: {json.dumps(datos, indent=2, ensure_ascii=False)}")
