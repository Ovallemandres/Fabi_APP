# Fabi_APP

Sistema de gestión, presupuestos y facturación de flotas (Django + PostgreSQL + Redis + Celery).

## Arranque local (backend)

1. **Crear entorno virtual e instalar dependencias**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. **Levantar PostgreSQL y Redis**

```powershell
docker compose up -d
```

3. **Configurar variables de entorno**

```powershell
copy .env.example .env
```

4. **Migrar, crear admin y correr el servidor**

```powershell
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

El MVP usa un único rol **admin** (`is_staff=True`). Todas las pantallas de negocio exigen login; `/health/` es público.

5. **Worker Celery** (otra terminal, con el venv activo)

```powershell
celery -A config worker -l info --pool=solo
```

En Windows usa `--pool=solo` (el pool prefork por defecto no es fiable aquí).

Smoke checks: `http://127.0.0.1:8000/health/` (público) y login en `/login/`.

### Emisor fiscal

Los datos del emisor (`CompanySettings`: razón social, RIF, dirección, IVA default) **solo se editan en** `/admin/`. No hay pantalla «Empresa» en la app; los PDF siguen leyendo esos datos.

### PDF (WeasyPrint)

En local puedes forzar generación en el request (sin worker) con `PDF_SYNC=True` en `.env`. Si el broker Redis no está disponible, el sistema también intenta generar el PDF de forma síncrona y muestra el error en mensajes si WeasyPrint falla.

En **Windows**, WeasyPrint suele fallar sin las librerías GTK/Pango (`libgobject-2.0-0`). La app usa automáticamente **xhtml2pdf** como fallback para que puedas descargar presupuestos y facturas en local. En Linux/Render se prefiere WeasyPrint cuando está disponible.

Worker opcional:

```powershell
celery -A config worker -l info --pool=solo
```

Tras migrar, crea el admin:

```powershell
python manage.py createsuperuser
```

### Sin Docker

Si no tienes Docker, necesitas PostgreSQL y Redis locales con las credenciales de `.env.example` (`fabi` / `fabi` / DB `fabi_dev`, Redis en `6379`).
