# API de tareas con Django REST Framework

Práctica de Desarrollo de Aplicaciones Web (IS093A), Universidad Nacional del Centro del Perú. La API permite listar, buscar y administrar tareas con periodos validados y enlaces a las operaciones.

## Puesta en marcha

Se verificó con Python 3.14 y Django 5.2. Usa Python 3.12 o posterior. Desde PowerShell, en la carpeta del repositorio, ejecuta:

```powershell
python -m venv .venv
$py = ".\.venv\Scripts\python.exe"
& $py -m pip install -r requirements.txt
& $py manage.py migrate
& $py manage.py check
$env:DJANGO_DEBUG = "1"
& $py manage.py runserver
```

Swagger está en [localhost:8000/api/docs/](http://localhost:8000/api/docs/). La [raíz de la API](http://localhost:8000/api/) ofrece el enlace a la colección y el [esquema OpenAPI](http://localhost:8000/api/schema/) describe sus operaciones.

## Rutas y permisos

| Método | Ruta | Acceso | Resultado |
| --- | --- | --- | --- |
| GET | `/api/` | Público | Raíz del router |
| GET | `/api/tareas/` | Público | Lista paginada |
| GET | `/api/tareas/{id}/` | Público | Detalle de una tarea |
| POST | `/api/tareas/` | Autenticado | Crea una tarea (201) |
| PUT / PATCH | `/api/tareas/{id}/` | Autenticado | Sustituye o actualiza una tarea |
| DELETE | `/api/tareas/{id}/` | Autenticado | Elimina una tarea (204) |
| POST | `/api/tareas/{id}/completar/` | Autenticado | Cambia el estado a `completado` |
| GET | `/api/csrf/` | Público | Emite el token CSRF y establece la cookie |

El recurso es compartido. Las cuentas autenticadas pueden editar las tareas del laboratorio. Los campos `id`, `url`, `created` y `completar_url` son de solo lectura. `periodo` contiene `inicio` y `fin` en formato ISO `YYYY-MM-DD`. Si el final precede al inicio, la API devuelve 400 con un error en `periodo.fin`.

La lista devuelve cinco tareas por página y los enlaces `next` y `previous`. Admite `status` (`activo` o `completado`), `search` (título y descripción), `page` y `ordering` (`created`, `titulo` o `fecha_fin`, con prefijo `-` para descendente). Los límites son 60 solicitudes por minuto por IP anónima y 120 por minuto por usuario autenticado. Al sobrepasarlos, la API responde 429 con `Retry-After`.

## Ejemplos con curl

Para escribir por token, crea primero una cuenta y luego un token en otra terminal. Usa los mismos comandos de PowerShell para definir `$py`.

```powershell
& $py manage.py createsuperuser --username estudiante
& $py manage.py drf_create_token estudiante
$token = Read-Host "Token de Django"
'{"titulo":"Preparar entrega","periodo":{"inicio":"2026-11-25","fin":"2026-11-27"}}' |
    curl.exe -i -X POST "http://localhost:8000/api/tareas/" `
    -H "Authorization: Token $token" -H "Content-Type: application/json" --data-binary "@-"
curl.exe -i "http://localhost:8000/api/tareas/?status=activo&page=2&ordering=-created"
```

Usa Swagger **Authorize** con el valor `Token <tu-token>` para enviar solicitudes autenticadas. Para sesión desde una SPA, autentica la sesión con el flujo de Django (en local está disponible `/api/auth/login/`). Solicita `GET /api/csrf/` con `credentials: 'include'` después de iniciar sesión y envía el valor `csrfToken` en `X-CSRFToken` junto con las cookies al escribir. Usa `localhost` para ambos puertos durante la práctica. Tanto CORS como CSRF permiten por defecto el origen `http://localhost:5173`.

```powershell
curl.exe -i -X OPTIONS "http://localhost:8000/api/tareas/" `
    -H "Origin: http://localhost:5173" `
    -H "Access-Control-Request-Method: POST" `
    -H "Access-Control-Request-Headers: content-type,x-csrftoken"
```

## Arquitectura y configuración

El cliente consume HTTP y JSON. El router asigna los métodos HTTP al ViewSet, el serializador valida y representa los datos, y el ORM aplica filtros e índices en la base de datos. La autenticación por token permite enviar credenciales en cada solicitud. El modo de sesión es opcional y usa cookies con CSRF. Los enlaces de la API permiten pasar de la colección al detalle o a la acción de completar. Una capa de proxy puede servir estáticos con caché y aplicar HTTPS. La respuesta que emite el token CSRF se marca `no-store`. El código descargable es una restricción opcional en REST y la API no depende de ella.

Para un despliegue, define `DJANGO_ENV=production`, `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CORS_ORIGINS` y `DJANGO_CSRF_ORIGINS` con valores del entorno. Activa `DJANGO_HTTPS=1` detrás de HTTPS para asegurar las cookies. Sirve los archivos de `collectstatic` con el proxy y carga `config.wsgi` o `config.asgi` en un servidor de aplicación. Puedes montar la base SQLite fuera del contenedor con `DJANGO_DB_PATH`. Para varios procesos, instala el cliente Python de Redis y configura `DJANGO_CACHE_LOCATION` para compartir los contadores de tasa.

## Pruebas y evidencias

```powershell
& $py manage.py test -v 2
& $py manage.py spectacular --validate --fail-on-warn --file schema.yaml
```

1. [Configuración y comprobación de Django](evidencias/01-configuracion.png)
2. [Validación anidada y respuesta hipervinculada](evidencias/02-serializacion.png)
3. [Router, detalle, acción y eliminación](evidencias/03-router.png)
4. [Filtrado, paginación y respuesta 429](evidencias/04-filtros.png)
5. [Swagger UI](evidencias/05-swagger.png) y [preflight CORS y verificación de CSRF](evidencias/06-cors-csrf.png)

[Repositorio de la práctica](https://github.com/taangel687-netizen/SEM13-AGUILAR1)

Referencias oficiales: [ViewSets de DRF](https://www.django-rest-framework.org/api-guide/viewsets/) y [drf-spectacular](https://drf-spectacular.readthedocs.io/en/latest/readme.html).
