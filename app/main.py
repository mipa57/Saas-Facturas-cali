# ============================================
# Servidor Principal - SaaS Facturas Cali
# ============================================

from fastapi import FastAPI, UploadFile, File, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import uvicorn
import os
import tempfile
import bcrypt
import secrets
from datetime import datetime
from dotenv import load_dotenv
from pydantic import BaseModel

from app.services.database import conectar_mongodb, coleccion_facturas, coleccion_empresas
from app.services.procesador import procesar_archivo, validar_nit
from app.services.claude_client import extraer_datos_factura

load_dotenv()

app = FastAPI(
    title="SaaS Facturas Cali",
    description="Procesamiento automático de facturas para PyMEs en Cali, Colombia",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# ============================================
# Modelos
# ============================================
class RegistroEmpresa(BaseModel):
    usuario: str
    contrasena: str
    nombre_negocio: str

class LoginEmpresa(BaseModel):
    usuario: str
    contrasena: str

# ============================================
# Helpers de autenticación
# ============================================
def hashear_contrasena(contrasena: str) -> str:
    return bcrypt.hashpw(contrasena.encode(), bcrypt.gensalt()).decode()

def verificar_contrasena(contrasena: str, hash_guardado: str) -> bool:
    return bcrypt.checkpw(contrasena.encode(), hash_guardado.encode())

def obtener_empresa_por_token(token: str) -> dict:
    """Busca la empresa asociada a un token de sesión."""
    col = coleccion_empresas()
    empresa = col.find_one({"token": token})
    if not empresa:
        raise HTTPException(status_code=401, detail="Sesión inválida. Inicia sesión nuevamente.")
    return empresa

# ============================================
# Startup
# ============================================
@app.on_event("startup")
async def startup():
    conectar_mongodb()
    print("🚀 SaaS Facturas Cali iniciado!")

# ============================================
# ENDPOINTS PÚBLICOS
# ============================================

@app.get("/")
async def inicio():
    return {
        "mensaje": "✅ SaaS Facturas Cali funcionando",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.get("/app")
async def frontend():
    return FileResponse("index.html")

# ============================================
# REGISTRO
# ============================================
@app.post("/registro")
async def registrar_empresa(datos: RegistroEmpresa):
    """Registra una nueva empresa en el sistema."""
    col = coleccion_empresas()

    # Verificar que el usuario no exista
    if col.find_one({"usuario": datos.usuario.lower().strip()}):
        raise HTTPException(status_code=400, detail="Ese nombre de usuario ya está en uso.")

    # Guardar empresa
    empresa = {
        "usuario":        datos.usuario.lower().strip(),
        "contrasena":     hashear_contrasena(datos.contrasena),
        "nombre_negocio": datos.nombre_negocio.strip(),
        "token":          None,
        "fecha_registro": datetime.now().isoformat()
    }
    col.insert_one(empresa)

    return {"exito": True, "mensaje": f"Empresa '{datos.nombre_negocio}' registrada correctamente."}

# ============================================
# LOGIN
# ============================================
@app.post("/login")
async def login(datos: LoginEmpresa):
    """Inicia sesión y retorna un token de sesión."""
    col = coleccion_empresas()
    empresa = col.find_one({"usuario": datos.usuario.lower().strip()})

    if not empresa or not verificar_contrasena(datos.contrasena, empresa["contrasena"]):
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos.")

    # Generar token de sesión
    token = secrets.token_hex(32)
    col.update_one({"_id": empresa["_id"]}, {"$set": {"token": token}})

    return {
        "exito": True,
        "token": token,
        "nombre_negocio": empresa["nombre_negocio"],
        "usuario": empresa["usuario"]
    }

# ============================================
# LOGOUT
# ============================================
@app.post("/logout")
async def logout(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Token requerido.")
    token = authorization.replace("Bearer ", "")
    coleccion_empresas().update_one({"token": token}, {"$set": {"token": None}})
    return {"exito": True, "mensaje": "Sesión cerrada."}

# ============================================
# SUBIR FACTURA (requiere login)
# ============================================
@app.post("/facturas/subir")
async def subir_factura(
    archivo: UploadFile = File(...),
    authorization: str = Header(None)
):
    if not authorization:
        raise HTTPException(status_code=401, detail="Debes iniciar sesión primero.")

    token = authorization.replace("Bearer ", "")
    empresa = obtener_empresa_por_token(token)

    tipos_permitidos = ["application/pdf", "image/jpeg", "image/png", "image/gif", "image/webp"]
    if archivo.content_type not in tipos_permitidos:
        raise HTTPException(status_code=400, detail=f"Tipo de archivo no permitido: {archivo.content_type}")

    try:
        sufijo = os.path.splitext(archivo.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=sufijo) as archivo_temp:
            contenido = await archivo.read()
            archivo_temp.write(contenido)
            ruta_temp = archivo_temp.name

        print(f"📄 Archivo recibido: {archivo.filename}")

        resultado_procesamiento = procesar_archivo(ruta_temp)

        if resultado_procesamiento["tipo"] == "pdf":
            datos_factura = extraer_datos_factura(texto=resultado_procesamiento["contenido"])
        else:
            datos_factura = extraer_datos_factura(
                imagen_base64=resultado_procesamiento["base64"],
                media_type=resultado_procesamiento["media_type"]
            )

        if "nit" in datos_factura:
            validacion = validar_nit(datos_factura["nit"])
            datos_factura["nit_valido"] = validacion["valido"]

        # Asociar factura a la empresa que la sube
        datos_factura["empresa_usuario"] = empresa["usuario"]
        datos_factura["empresa_nombre"]  = empresa["nombre_negocio"]
        datos_factura["archivo_original"] = archivo.filename
        datos_factura["fecha_procesado"]  = datetime.now().isoformat()
        datos_factura["estado"]           = "procesada"

        coleccion = coleccion_facturas()
        resultado = coleccion.insert_one(datos_factura)
        os.unlink(ruta_temp)

        print(f"✅ Factura guardada: {resultado.inserted_id}")

        return {
            "exito": True,
            "mensaje": "Factura procesada correctamente",
            "id": str(resultado.inserted_id),
            "datos": {
                "proveedor": datos_factura.get("proveedor", ""),
                "nit":       datos_factura.get("nit", ""),
                "total":     datos_factura.get("total", 0),
                "fecha":     datos_factura.get("fecha", ""),
                "nit_valido": datos_factura.get("nit_valido", False)
            }
        }

    except Exception as e:
        print(f"❌ Error procesando factura: {e}")
        raise HTTPException(status_code=500, detail=f"Error procesando factura: {str(e)}")

# ============================================
# LISTAR FACTURAS (solo las de la empresa)
# ============================================
@app.get("/facturas")
async def listar_facturas(limite: int = 20, authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Debes iniciar sesión primero.")

    token = authorization.replace("Bearer ", "")
    empresa = obtener_empresa_por_token(token)

    try:
        coleccion = coleccion_facturas()
        facturas_raw = list(
            coleccion.find({"empresa_usuario": empresa["usuario"]})
            .limit(limite)
            .sort("fecha_procesado", -1)
        )
        facturas = []
        for f in facturas_raw:
            f["_id"] = str(f["_id"])
            facturas.append(f)

        return {"total": len(facturas), "facturas": facturas}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listando facturas: {str(e)}")

# ============================================
# Iniciar servidor
# ============================================
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)