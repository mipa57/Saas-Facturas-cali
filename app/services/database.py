# ============================================
# Conexión con MongoDB Atlas
# SaaS Facturas Cali
# ============================================

from pymongo import MongoClient
from pymongo.collection import Collection
from dotenv import load_dotenv
import os

load_dotenv()

MONGODB_URI      = os.getenv("MONGODB_URI")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "saas_facturas_cali")

cliente_mongo = None
base_datos    = None

def conectar_mongodb():
    global cliente_mongo, base_datos
    try:
        cliente_mongo = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=10000)
        base_datos    = cliente_mongo[MONGODB_DATABASE]
        cliente_mongo.admin.command('ping')
        print(f"✅ Conectado a MongoDB: {MONGODB_DATABASE}")
        return True
    except Exception as e:
        print(f"❌ Error conectando a MongoDB: {e}")
        return False

def obtener_coleccion(nombre: str) -> Collection:
    if base_datos is None:
        conectar_mongodb()
    return base_datos[nombre]

def cerrar_mongodb():
    global cliente_mongo
    if cliente_mongo:
        cliente_mongo.close()
        print("✅ Conexión MongoDB cerrada")

def coleccion_facturas():
    return obtener_coleccion("facturas")

def coleccion_clientes():
    return obtener_coleccion("clientes")

def coleccion_empresas():
    return obtener_coleccion("empresas")

def coleccion_pagos():
    return obtener_coleccion("pagos")