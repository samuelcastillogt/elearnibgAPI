from pathlib import Path
import os
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel


class Course(BaseModel):
    id: int
    slug: str
    title: str
    category: str
    progress: int

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent.parent
FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"

app = FastAPI(title="Escuela API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def _normalize_course(payload: dict[str, Any]) -> Course:
    return Course(
        id=int(payload["id"]),
        slug=str(payload["slug"]),
        title=str(payload["title"]),
        category=str(payload["category"]),
        progress=int(payload.get("progress", 0)),
    )


async def _fetch_courses_from_supabase() -> list[Course]:
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")
    table_name = os.getenv("SUPABASE_COURSES_TABLE", "courses")

    if not supabase_url or not supabase_key:
        raise HTTPException(
            status_code=500,
            detail="SUPABASE_URL y SUPABASE_ANON_KEY son requeridos en el backend.",
        )

    endpoint = f"{supabase_url.rstrip('/')}/rest/v1/{table_name}"
    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
        "Accept": "application/json",
    }
    params = {
        "select": "id,slug,title,category,progress",
        "order": "id.asc",
    }

    try:
        async with httpx.AsyncClient(timeout=12) as client:
            response = await client.get(endpoint, headers=headers, params=params)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="No se pudo conectar a Supabase.") from exc

    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail="Supabase devolvio un error al consultar cursos.")

    data = response.json()
    if not isinstance(data, list):
        raise HTTPException(status_code=502, detail="Respuesta invalida de Supabase.")

    try:
        return [_normalize_course(item) for item in data]
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="Los cursos en Supabase tienen un formato invalido.") from exc


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/courses", response_model=list[Course])
async def list_courses() -> list[Course]:
    return await _fetch_courses_from_supabase()


if FRONTEND_DIST.exists():
    app.mount("/app", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend-app")
else:

    @app.get("/app", response_class=HTMLResponse)
    def app_not_built():
        return """
        <h1>Frontend no compilado</h1>
        <p>Ejecuta <code>cd frontend && npm run build</code> para generar la app de React.</p>
        """
