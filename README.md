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

4. **Migrar y correr el servidor**

```powershell
python manage.py migrate
python manage.py runserver
```

5. **Worker Celery** (otra terminal, con el venv activo)

```powershell
celery -A config worker -l info --pool=solo
```

En Windows usa `--pool=solo` (el pool prefork por defecto no es fiable aquí).

Smoke checks: `http://127.0.0.1:8000/` y `http://127.0.0.1:8000/health/`

### Sin Docker

Si no tienes Docker, necesitas PostgreSQL y Redis locales con las credenciales de `.env.example` (`fabi` / `fabi` / DB `fabi_dev`, Redis en `6379`).
