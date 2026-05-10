# 📄 SaaS Facturas Cali

Sistema de automatización de procesamiento de facturas electrónicas para PyMEs en Cali, Colombia. Usa inteligencia artificial (Claude API de Anthropic) para extraer automáticamente los datos de facturas en PDF o imagen.

## 🌐 URL en producción

```
https://saas-facturas-cali-production.up.railway.app/app
```

API:
```
https://saas-facturas-cali-production.up.railway.app
```

---

## ¿Qué hace?

- Recibe facturas en PDF, JPG o PNG
- Extrae automáticamente: proveedor, NIT, fecha, total y productos
- Valida el NIT colombiano (formato XXXXXXXXX-X)
- Guarda todo en MongoDB Atlas
- Muestra el historial de facturas procesadas

---

## 🛠 Stack tecnológico

| Capa | Tecnología |
|------|-----------|
| API | FastAPI + Uvicorn |
| IA | Claude API (claude-haiku-4-5) |
| Base de datos | MongoDB Atlas |
| Lectura PDFs | pdfplumber |
| Frontend | HTML + CSS + JS vanilla |
| Hosting | Railway |

---

## 📁 Estructura del proyecto

```
Saas-Facturas-cali/
├── app/
│   ├── main.py              # Endpoints FastAPI
│   └── services/
│       ├── claude_client.py # Integración con Claude API
│       ├── database.py      # Conexión MongoDB
│       └── procesador.py    # Lectura de PDFs e imágenes
├── index.html               # Frontend
├── run.py                   # Arranque local
├── nixpacks.toml            # Configuración Railway
├── requirements.txt
└── .env.example
```

---

## ⚙️ Variables de entorno

Crea un archivo `.env` basado en `.env.example`:

```env
ANTHROPIC_API_KEY=sk-ant-...
MONGODB_URI=mongodb+srv://...
MONGODB_DATABASE=saas_facturas_cali
MODO_DEMO=true   # cambiar a false cuando haya créditos en Anthropic
```

---

## 🚀 Correr en local

```bash
# Instalar dependencias
pip install -r requirements.txt

# Iniciar servidor
python run.py
```

Abrir en el navegador:
- API: `http://localhost:8000`
- Frontend: `http://localhost:8000/app`
- Docs interactivos: `http://localhost:8000/docs`

---

## 📡 Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/` | Estado del servidor |
| GET | `/app` | Frontend web |
| POST | `/facturas/subir` | Subir y procesar una factura |
| GET | `/facturas` | Listar facturas procesadas |
| GET | `/facturas/buscar/{nit}` | Buscar por NIT |

---

## 🇨🇴 Mercado objetivo

- 8.900 PyMEs en Cali, Colombia
- Sectores: comercio, gastronomía, servicios
- Precio: $35.000 – $180.000 COP/mes

---

## 👤 Desarrollador

**Miguel Gustavo Bejarano Patiño**  
Cali, Valle del Cauca, Colombia  
GitHub: [@mipa57](https://github.com/mipa57)  
WhatsApp: [+57 304 247 5687](https://wa.me/573042475687)  
Correo: mipa57125@gmail.com