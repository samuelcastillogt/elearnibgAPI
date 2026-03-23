# Backoffice de cursos

Implementacion de EL-20 para publicacion y administracion de cursos en la ruta `/bo/`.

## Objetivo

Separar la gestion de cursos de la experiencia del alumno, con una interfaz de backoffice para:

- Crear cursos.
- Administrar cursos existentes.
- Controlar estado de publicacion.

## Frontend

- Ruta base: `/bo/`.
- Navegacion lateral con dos opciones:
  - `Crear curso` (`/bo/create-course`)
  - `Administrar cursos` (`/bo/manage-courses`)

### Pantallas

1. **Crear curso**
   - Formulario con `title`, `category`, `progress`, `published`.
   - Guarda mediante `POST /api/backoffice/courses`.

2. **Administrar cursos**
   - Tabla con listado completo de cursos.
   - Permite publicar/despublicar con `PATCH /api/backoffice/courses/{id}`.

## Backend

### Endpoints

- `GET /api/backoffice/courses`
  - Devuelve todos los cursos (incluyendo no publicados).

- `POST /api/backoffice/courses`
  - Crea curso nuevo.
  - Genera `slug` automaticamente si no se envia.

- `PATCH /api/backoffice/courses/{course_id}`
  - Actualiza campos del curso (`title`, `category`, `progress`, `published`).

- `GET /api/courses`
  - Para la app de alumnos devuelve solo cursos publicados.

## Modelo de publicacion

Se agrega `published boolean` en `courses`:

- `true`: visible en la plataforma del alumno.
- `false`: oculto para alumnos, visible solo en backoffice.

## Migracion

- Archivo: `backend/db/migrations/20260323_el20_backoffice_courses.sql`
- Incluye:
  - `alter table` para `courses.published`
  - tablas `classes`, `course_student`, `classes_student`
  - indices recomendados
