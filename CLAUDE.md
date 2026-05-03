# SaaS Facturas Cali - Contexto del Proyecto

## Descripción
Sistema de automatización de procesamiento de facturas 
electrónicas para PyMEs en Cali, Colombia.

## Desarrollador
- Nombre: Miguel Gustavo Bejarano Patiño
- Nivel: Principiante-Intermedio en Python
- Ciudad: Cali, Valle del Cauca, Colombia
- GitHub: github.com/mipa57

## Stack Tecnológico
- Lenguaje: Python 3.11
- API Web: FastAPI + Uvicorn
- Base de datos: MongoDB Atlas
- IA: Claude API (Anthropic) - modelo claude-haiku-4-5-20251001
- Lectura PDFs: pdfplumber
- Variables entorno: python-dotenv

## Mercado Objetivo
- 117.000 empresas registradas en Cali
- 8.900 PyMEs potenciales
- Sectores: comercio (41.759) y gastronomía (10.028)
- Precio: $35.000 - $180.000 COP/mes

## Competencia
- Alegra: desde $17.900/mes
- Siigo: desde $145.993/mes
- NUESTRO PRECIO: $35.000 - $180.000 COP/mes

## Convenciones de Código
- Todo en español (variables, funciones, comentarios)
- Indentación: 4 espacios
- Funciones: snake_case en español
- Siempre validar NIT colombiano (XXXXXXXXX-X)
- Temperature 0 para extracción de datos

## Variables de Entorno
- ANTHROPIC_API_KEY
- MONGODB_URI
- MONGODB_DATABASE: saas_facturas_cali

## Reglas
- NUNCA subir .env a GitHub
- SIEMPRE Temperature 0 para extracción
- SIEMPRE validar NIT antes de guardar
