# ============================================
# Conexión con MongoDB Atlas
# SaaS Facturas Cali
# ============================================

from pymongo import MongoClient
from pymongo.collection import Collection
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

# Variables de conexión
MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "saas_facturas_cali")

# Cliente global de MongoDB
cliente_mongo = None
base_datos = None

def conectar_mongodb():
    global cliente_mongo, base_datos
    
    try:
        # Conexión con SSL para Windows 10
        cliente_mongo = MongoClient(
            MONGODB_URI,
            tls=True,
            tlsAllowInvalidCertificates=True,
            serverSelectionTimeoutMS=10000
        )
        base_datos = cliente_mongo[MONGODB_DATABASE]
        
        # Verificar conexión
        cliente_mongo.admin.command('ping')
        print(f"✅ Conectado a MongoDB: {MONGODB_DATABASE}")
        return True
        
    except Exception as e:
        print(f"❌ Error conectando a MongoDB: {e}")
        return False

def obtener_coleccion(nombre_coleccion: str) -> Collection:
    if base_datos is None:
        conectar_mongodb()
    return base_datos[nombre_coleccion]

def cerrar_mongodb():
    global cliente_mongo
    if cliente_mongo:
        cliente_mongo.close()
        print("✅ Conexión MongoDB cerrada")

def coleccion_facturas():
    return obtener_coleccion("facturas")

def coleccion_clientes():
    return obtener_coleccion("clientes")

def coleccion_pagos():
    return obtener_coleccion("pagos")

if __name__ == "__main__":
    if conectar_mongodb():
        print("✅ Conexión exitosa!")
        coleccion = coleccion_facturas()
        resultado = coleccion.insert_one({
            "prueba": True,
            "mensaje": "Conexión exitosa desde SaaS Facturas Cali"
        })
        print(f"✅ Documento insertado: {resultado.inserted_id}")
        coleccion.delete_one({"prueba": True})
        print("✅ Prueba limpiada")
        cerrar_mongodb()
    else:
        print("❌ No se pudo conectar a MongoDB")
