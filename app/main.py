# ============================================
# Servidor Principal - SaaS Facturas Cali
# ============================================

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
import tempfile
from datetime import datetime
from dotenv import load_dotenv

# Importar servicios propios
from app.services.database import conectar_mongodb, coleccion_facturas, coleccion_clientes
from app.services.procesador import procesar_archivo, validar_nit
from app.services.claude_client import extraer_datos_factura

# Cargar variables de entorno
load_dotenv()

# ============================================
# Crear aplicación FastAPI
# ============================================
app = FastAPI(
    title="SaaS Facturas Cali",
    description="Procesamiento automático de facturas para PyMEs en Cali, Colombia",
    version="1.0.0"
)

# Permitir peticiones desde el navegador
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# ============================================
# Conectar MongoDB al iniciar
# ============================================
@app.on_event("startup")
async def startup():
    conectar_mongodb()
    print("🚀 SaaS Facturas Cali iniciado!")

# ============================================
# ENDPOINTS
# ============================================

@app.get("/")
async def inicio():
    """Endpoint de bienvenida"""
    return {
        "mensaje": "✅ SaaS Facturas Cali funcionando",
        "version": "1.0.0",
        "endpoints": {
            "subir_factura": "/facturas/subir",
            "listar_facturas": "/facturas",
            "ver_factura": "/facturas/{id}"
        }
    }

@app.get("/health")
async def health_check():
    """Verificar que el servidor está funcionando"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.post("/facturas/subir")
async def subir_factura(
    archivo: UploadFile = File(...),
    nit_cliente: str = None
):
    """
    Sube y procesa una factura (PDF o imagen)
    
    - archivo: PDF, JPG, PNG de la factura
    - nit_cliente: NIT del cliente que sube la factura
    """
    
    # Validar tipo de archivo
    tipos_permitidos = [
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp"
    ]
    
    if archivo.content_type not in tipos_permitidos:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de archivo no permitido: {archivo.content_type}"
        )
    
    try:
        # Guardar archivo temporalmente
        sufijo = os.path.splitext(archivo.filename)[1]
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=sufijo
        ) as archivo_temp:
            contenido = await archivo.read()
            archivo_temp.write(contenido)
            ruta_temp = archivo_temp.name
        
        print(f"📄 Archivo recibido: {archivo.filename}")
        
        # Procesar archivo
        resultado_procesamiento = procesar_archivo(ruta_temp)
        
        # Extraer datos con Claude
        if resultado_procesamiento["tipo"] == "pdf":
            datos_factura = extraer_datos_factura(
                resultado_procesamiento["contenido"]
            )
        else:
            # Imágenes: enviar base64 real a Claude
            datos_factura = extraer_datos_factura(
            imagen_base64=resultado_procesamiento["base64"],
            media_type=resultado_procesamiento["media_type"]
    )
        
        # Validar NIT extraído
        if "nit" in datos_factura:
            validacion = validar_nit(datos_factura["nit"])
            datos_factura["nit_valido"] = validacion["valido"]
        
        # Agregar metadata
        datos_factura["archivo_original"] = archivo.filename
        datos_factura["fecha_procesado"] = datetime.now().isoformat()
        datos_factura["nit_cliente"] = nit_cliente
        datos_factura["estado"] = "procesada"
        
        # Guardar en MongoDB
        coleccion = coleccion_facturas()
        resultado = coleccion.insert_one(datos_factura)
        
        # Limpiar archivo temporal
        os.unlink(ruta_temp)
        
        print(f"✅ Factura guardada: {resultado.inserted_id}")
        
        return {
            "exito": True,
            "mensaje": "Factura procesada correctamente",
            "id": str(resultado.inserted_id),
            "datos": {
                "proveedor": datos_factura.get("proveedor", ""),
                "nit": datos_factura.get("nit", ""),
                "total": datos_factura.get("total", 0),
                "fecha": datos_factura.get("fecha", ""),
                "nit_valido": datos_factura.get("nit_valido", False)
            }
        }
        
    except Exception as e:
        print(f"❌ Error procesando factura: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error procesando factura: {str(e)}"
        )

@app.get("/facturas")
async def listar_facturas(limite: int = 10):
    """Lista las últimas facturas procesadas"""
    try:
        coleccion = coleccion_facturas()
        facturas_raw = list(
            coleccion.find({}).limit(limite).sort("fecha_procesado", -1)
        )
        # Convertir ObjectId a string para poder serializar a JSON
        facturas = []
        for f in facturas_raw:
            f["_id"] = str(f["_id"])
            facturas.append(f)
        
        return {
            "total": len(facturas),
            "facturas": facturas
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listando facturas: {str(e)}"
        )

@app.get("/facturas/buscar/{nit}")
async def buscar_por_nit(nit: str):
    """Busca facturas por NIT del proveedor"""
    try:
        # Validar NIT
        validacion = validar_nit(nit)
        if not validacion["valido"]:
            raise HTTPException(
                status_code=400,
                detail=validacion["mensaje"]
            )
        
        coleccion = coleccion_facturas()
        facturas = list(
            coleccion.find(
                {"nit": nit},
                {"_id": 0}
            )
        )
        
        return {
            "nit": nit,
            "total_facturas": len(facturas),
            "facturas": facturas
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error buscando facturas: {str(e)}"
        )

# ============================================
# Iniciar servidor
# ============================================
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )