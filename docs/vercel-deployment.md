# Despliegue en Vercel

Este proyecto queda preparado para desplegar frontend + API en un solo proyecto de Vercel.

## Estructura usada

- `frontend/`: app React (Vite)
- `api/index.py`: entrypoint serverless para FastAPI
- `backend/app/main.py`: API principal
- `vercel.json`: rutas/build para frontend y backend

## Variables de entorno en Vercel

Configura estas variables en el proyecto:

- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SCHEMA` (opcional, default `public`)
- `SUPABASE_COURSES_TABLE` (opcional, default `courses`)
- `VITE_API_URL` (recomendado dejar vacia para usar mismo dominio)

## Notas de build

- En Vercel, el build del frontend usa `frontend/package.json` y genera `frontend/dist`.
- La API se publica como function Python desde `api/index.py`.
- Las rutas `/api/*` se enrutan a FastAPI.
- El resto de rutas usan fallback SPA hacia `index.html`.

## Build local para backend (modo legado)

Si quieres que el backend local sirva el frontend en `/app/`, usa:

```bash
cd frontend
npm run build:backend
```

Para despliegue en Vercel no hace falta ese modo; se usa base `/`.

## Si solo despliegas el repo `backend`

Si tu proyecto de Vercel apunta unicamente al repo `backend`, la API no tendra acceso a `../frontend/dist`.

En ese caso debes copiar el build del frontend dentro del repo backend en una de estas rutas:

1. `backend/app/static/app` (recomendada)
2. `backend/frontend/dist`

Comando sugerido (desde la raiz monorepo):

```bash
cd frontend && npm run build && mkdir -p ../backend/app/static/app && cp -R dist/. ../backend/app/static/app/
```

Con eso, la ruta `/app` sera servida por FastAPI desde el backend desplegado.
