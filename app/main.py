import os
import re
import secrets
from datetime import datetime, timezone
from pathlib import Path
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
    published: bool = True


class CreateCoursePayload(BaseModel):
    title: str
    category: str
    progress: int = 0
    published: bool = False
    slug: str | None = None


class UpdateCoursePayload(BaseModel):
    title: str | None = None
    category: str | None = None
    progress: int | None = None
    published: bool | None = None


class CourseClass(BaseModel):
    id: int
    id_curso: int
    nombre_clase: str
    descripcion: str
    url_video: str


class StudentClass(BaseModel):
    id: int
    id_curso: int
    id_clase: int
    id_alumno: str
    time: int
    status: bool
    nombre_clase: str
    descripcion: str
    url_video: str


class CourseStudent(BaseModel):
    id: int
    id_alumno: str
    id_curso: int
    status: bool
    id_certificado: str | None
    fecha_asignacion: str
    fecha_finalizado: str | None


class CourseProgress(BaseModel):
    course: Course
    enrollment: CourseStudent
    classes: list[StudentClass]
    completed_classes: int
    pending_classes: int
    action_label: str

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
        published=bool(payload.get("published", True)),
    )


def _slugify(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    if not normalized:
        raise HTTPException(status_code=400, detail="No se pudo generar un slug valido para el curso.")
    return normalized


def _normalize_class(payload: dict[str, Any]) -> CourseClass:
    return CourseClass(
        id=int(payload["id"]),
        id_curso=int(payload["id_curso"]),
        nombre_clase=str(payload["nombre_clase"]),
        descripcion=str(payload.get("descripcion") or ""),
        url_video=str(payload.get("url_video") or ""),
    )


def _normalize_course_student(payload: dict[str, Any]) -> CourseStudent:
    return CourseStudent(
        id=int(payload["id"]),
        id_alumno=str(payload["id_alumno"]),
        id_curso=int(payload["id_curso"]),
        status=bool(payload.get("status", False)),
        id_certificado=(str(payload["id_certificado"]) if payload.get("id_certificado") else None),
        fecha_asignacion=str(payload.get("fecha_asignacion") or ""),
        fecha_finalizado=(str(payload["fecha_finalizado"]) if payload.get("fecha_finalizado") else None),
    )


def _normalize_student_class(payload: dict[str, Any], classes_map: dict[int, CourseClass]) -> StudentClass:
    class_id = int(payload["id_clase"])
    course_class = classes_map.get(class_id)

    if not course_class:
        raise HTTPException(status_code=502, detail="Hay registros de clases sin definicion en classes.")

    return StudentClass(
        id=int(payload["id"]),
        id_curso=int(payload["id_curso"]),
        id_clase=class_id,
        id_alumno=str(payload["id_alumno"]),
        time=int(payload.get("time", 0)),
        status=bool(payload.get("status", False)),
        nombre_clase=course_class.nombre_clase,
        descripcion=course_class.descripcion,
        url_video=course_class.url_video,
    )


def _build_action_label(enrollment_status: bool, pending_classes: int, completed_classes: int) -> str:
    if enrollment_status and pending_classes == 0:
        return "Ver certificado"
    if completed_classes > 0:
        return "Continuar"
    return "Iniciar curso"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _generate_certificate_code(course_id: int, student_uid: str) -> str:
    random_part = secrets.token_hex(4).upper()
    uid_suffix = student_uid.replace("-", "")[-6:].upper()
    return f"CERT-{course_id}-{uid_suffix}-{random_part}"


def _get_supabase_config() -> tuple[str, str, str]:
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")
    schema_name = os.getenv("SUPABASE_SCHEMA", "public")

    if not supabase_url or not supabase_key:
        raise HTTPException(
            status_code=500,
            detail="SUPABASE_URL y SUPABASE_ANON_KEY son requeridos en el backend.",
        )

    return supabase_url.rstrip("/"), supabase_key, schema_name


async def _supabase_request(
    *,
    method: str,
    table_name: str,
    params: dict[str, str] | None = None,
    payload: Any | None = None,
    prefer: str | None = None,
) -> list[dict[str, Any]]:
    supabase_url, supabase_key, schema_name = _get_supabase_config()
    endpoint = f"{supabase_url}/rest/v1/{table_name}"

    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Accept-Profile": schema_name,
    }

    if prefer:
        headers["Prefer"] = prefer

    if method in {"POST", "PATCH", "PUT", "DELETE"}:
        headers["Content-Profile"] = schema_name

    try:
        async with httpx.AsyncClient(timeout=12) as client:
            response = await client.request(method, endpoint, headers=headers, params=params, json=payload)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="No se pudo conectar a Supabase.") from exc

    if response.status_code >= 400:
        raise HTTPException(
            status_code=502,
            detail=f"Supabase devolvio un error al consultar {table_name}.",
        )

    if not response.content:
        return []

    data = response.json()
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return [data]

    raise HTTPException(status_code=502, detail="Respuesta invalida de Supabase.")


async def _fetch_courses_from_supabase(
    course_ref: str | None = None,
    include_unpublished: bool = False,
) -> list[Course]:
    table_name = os.getenv("SUPABASE_COURSES_TABLE", "courses")
    params = {
        "select": "id,slug,title,category,progress,published",
        "order": "id.asc",
    }

    if not include_unpublished:
        params["published"] = "eq.true"

    if course_ref:
        if course_ref.isdigit():
            params["id"] = f"eq.{course_ref}"
        else:
            params["slug"] = f"eq.{course_ref}"

    data = await _supabase_request(method="GET", table_name=table_name, params=params)

    try:
        return [_normalize_course(item) for item in data]
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="Los cursos en Supabase tienen un formato invalido.") from exc


async def _fetch_classes_for_course(course_id: int) -> list[CourseClass]:
    raw_classes = await _supabase_request(
        method="GET",
        table_name="classes",
        params={
            "select": "id,id_curso,nombre_clase,descripcion,url_video",
            "id_curso": f"eq.{course_id}",
            "order": "id.asc",
        },
    )

    if not raw_classes:
        raise HTTPException(status_code=404, detail="Este curso no tiene clases configuradas.")

    try:
        return [_normalize_class(item) for item in raw_classes]
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="Las clases del curso tienen un formato invalido.") from exc


async def _ensure_student_progress(course: Course, student_uid: str) -> CourseProgress:
    classes = await _fetch_classes_for_course(course.id)

    raw_enrollment = await _supabase_request(
        method="GET",
        table_name="course_student",
        params={
            "select": "id,id_alumno,id_curso,status,id_certificado,fecha_asignacion,fecha_finalizado",
            "id_curso": f"eq.{course.id}",
            "id_alumno": f"eq.{student_uid}",
            "limit": "1",
        },
    )

    if raw_enrollment:
        enrollment = _normalize_course_student(raw_enrollment[0])
    else:
        created_enrollment = await _supabase_request(
            method="POST",
            table_name="course_student",
            payload={
                "id_alumno": student_uid,
                "id_curso": course.id,
                "status": False,
            },
            prefer="return=representation",
        )

        enrollment = _normalize_course_student(created_enrollment[0])

    raw_student_classes = await _supabase_request(
        method="GET",
        table_name="classes_student",
        params={
            "select": "id,id_curso,id_clase,id_alumno,time,status",
            "id_curso": f"eq.{course.id}",
            "id_alumno": f"eq.{student_uid}",
            "order": "id_clase.asc",
        },
    )

    existing_class_ids = {int(item["id_clase"]) for item in raw_student_classes}
    missing_class_records = [
        {
            "id_curso": course.id,
            "id_clase": course_class.id,
            "id_alumno": student_uid,
            "time": 0,
            "status": False,
        }
        for course_class in classes
        if course_class.id not in existing_class_ids
    ]

    if missing_class_records:
        await _supabase_request(
            method="POST",
            table_name="classes_student",
            payload=missing_class_records,
            prefer="resolution=merge-duplicates,return=representation",
        )

        raw_student_classes = await _supabase_request(
            method="GET",
            table_name="classes_student",
            params={
                "select": "id,id_curso,id_clase,id_alumno,time,status",
                "id_curso": f"eq.{course.id}",
                "id_alumno": f"eq.{student_uid}",
                "order": "id_clase.asc",
            },
        )

    classes_map = {course_class.id: course_class for course_class in classes}
    student_classes = [_normalize_student_class(item, classes_map) for item in raw_student_classes]

    completed_classes = sum(1 for item in student_classes if item.status)
    pending_classes = len(student_classes) - completed_classes

    if pending_classes == 0 and not enrollment.status:
        certificate_code = _generate_certificate_code(course.id, student_uid)
        updated_enrollment_raw = await _supabase_request(
            method="PATCH",
            table_name="course_student",
            params={"id": f"eq.{enrollment.id}"},
            payload={
                "status": True,
                "id_certificado": certificate_code,
                "fecha_finalizado": _iso_now(),
            },
            prefer="return=representation",
        )
        enrollment = _normalize_course_student(updated_enrollment_raw[0])

    action_label = _build_action_label(enrollment.status, pending_classes, completed_classes)

    return CourseProgress(
        course=course,
        enrollment=enrollment,
        classes=student_classes,
        completed_classes=completed_classes,
        pending_classes=pending_classes,
        action_label=action_label,
    )


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/courses", response_model=list[Course])
async def list_courses() -> list[Course]:
    return await _fetch_courses_from_supabase()


@app.get("/api/courses/{course_ref}", response_model=Course)
async def get_course(course_ref: str) -> Course:
    courses = await _fetch_courses_from_supabase(course_ref=course_ref)
    if not courses:
        raise HTTPException(status_code=404, detail="No encontramos ese curso.")

    return courses[0]


@app.get("/api/courses/{course_ref}/students/{student_uid}/progress", response_model=CourseProgress)
async def get_course_progress(course_ref: str, student_uid: str) -> CourseProgress:
    if not student_uid.strip():
        raise HTTPException(status_code=400, detail="El id del alumno es obligatorio.")

    courses = await _fetch_courses_from_supabase(course_ref=course_ref)
    if not courses:
        raise HTTPException(status_code=404, detail="No encontramos ese curso.")

    return await _ensure_student_progress(courses[0], student_uid.strip())


@app.get("/api/backoffice/courses", response_model=list[Course])
async def list_backoffice_courses() -> list[Course]:
    return await _fetch_courses_from_supabase(include_unpublished=True)


@app.post("/api/backoffice/courses", response_model=Course)
async def create_backoffice_course(payload: CreateCoursePayload) -> Course:
    title = payload.title.strip()
    category = payload.category.strip()

    if not title or not category:
        raise HTTPException(status_code=400, detail="Titulo y categoria son obligatorios.")

    if payload.progress < 0 or payload.progress > 100:
        raise HTTPException(status_code=400, detail="El progreso debe estar entre 0 y 100.")

    course_slug = _slugify(payload.slug.strip() if payload.slug else title)

    created = await _supabase_request(
        method="POST",
        table_name=os.getenv("SUPABASE_COURSES_TABLE", "courses"),
        payload={
            "slug": course_slug,
            "title": title,
            "category": category,
            "progress": payload.progress,
            "published": payload.published,
        },
        prefer="return=representation",
    )

    try:
        return _normalize_course(created[0])
    except (IndexError, KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="No se pudo normalizar el curso creado.") from exc


@app.patch("/api/backoffice/courses/{course_id}", response_model=Course)
async def update_backoffice_course(course_id: int, payload: UpdateCoursePayload) -> Course:
    if course_id <= 0:
        raise HTTPException(status_code=400, detail="El id del curso es invalido.")

    updates: dict[str, Any] = {}

    if payload.title is not None:
        title = payload.title.strip()
        if not title:
            raise HTTPException(status_code=400, detail="El titulo no puede quedar vacio.")
        updates["title"] = title

    if payload.category is not None:
        category = payload.category.strip()
        if not category:
            raise HTTPException(status_code=400, detail="La categoria no puede quedar vacia.")
        updates["category"] = category

    if payload.progress is not None:
        if payload.progress < 0 or payload.progress > 100:
            raise HTTPException(status_code=400, detail="El progreso debe estar entre 0 y 100.")
        updates["progress"] = payload.progress

    if payload.published is not None:
        updates["published"] = payload.published

    if not updates:
        raise HTTPException(status_code=400, detail="No se recibieron cambios para actualizar.")

    updated = await _supabase_request(
        method="PATCH",
        table_name=os.getenv("SUPABASE_COURSES_TABLE", "courses"),
        params={"id": f"eq.{course_id}"},
        payload=updates,
        prefer="return=representation",
    )

    if not updated:
        raise HTTPException(status_code=404, detail="No encontramos el curso a actualizar.")

    try:
        return _normalize_course(updated[0])
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="No se pudo normalizar el curso actualizado.") from exc


@app.post(
    "/api/courses/{course_ref}/students/{student_uid}/classes/{class_id}/complete",
    response_model=CourseProgress,
)
async def complete_class(course_ref: str, student_uid: str, class_id: int) -> CourseProgress:
    if class_id <= 0:
        raise HTTPException(status_code=400, detail="El id de la clase es invalido.")

    courses = await _fetch_courses_from_supabase(course_ref=course_ref)
    if not courses:
        raise HTTPException(status_code=404, detail="No encontramos ese curso.")

    course = courses[0]
    progress = await _ensure_student_progress(course, student_uid.strip())

    target_class = next((item for item in progress.classes if item.id_clase == class_id), None)
    if not target_class:
        raise HTTPException(status_code=404, detail="No encontramos esa clase para este alumno.")

    if not target_class.status:
        await _supabase_request(
            method="PATCH",
            table_name="classes_student",
            params={"id": f"eq.{target_class.id}"},
            payload={
                "status": True,
                "time": max(target_class.time, 1),
            },
            prefer="return=representation",
        )

    return await _ensure_student_progress(course, student_uid.strip())


if FRONTEND_DIST.exists():
    app.mount("/app", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend-app")
else:

    @app.get("/app", response_class=HTMLResponse)
    def app_not_built():
        return """
        <h1>Frontend no compilado</h1>
        <p>Ejecuta <code>cd frontend && npm run build</code> para generar la app de React.</p>
        """
