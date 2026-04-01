# Backoffice de cursos

Implementacion de EL-20 para publicacion y administracion de cursos en la ruta `/bo/`.

## Objetivo

Separar la gestion de cursos de la experiencia del alumno, con una interfaz de backoffice para:

- Crear cursos.
- Agregar clases asociadas al curso recien creado.
- Administrar cursos existentes.
- Controlar estado de publicacion.

## Frontend

- Ruta base: `/bo/`.
- Navegacion lateral con tres opciones:
  - `Crear curso` (`/bo/create-course`)
  - `Administrar cursos` (`/bo/manage-courses`)
  - `Gestionar clases` (`/bo/manage-classes`)

### Pantallas

1. **Crear curso**
   - Formulario con `title`, `category`, `progress`, `published`.
   - Guarda mediante `POST /api/backoffice/courses`.
   - Luego habilita un formulario para crear clases con `nombre_clase`, `descripcion`, `url_video`.
   - Carga y muestra las clases existentes del curso recien creado.
   - Permite editar o eliminar clases del curso desde la misma pantalla.
   - Cada clase se guarda asociada al `id` del curso en la tabla `classes`.

2. **Administrar cursos**
   - Tabla con listado completo de cursos.
   - Permite publicar/despublicar con `PATCH /api/backoffice/courses/{id}`.
   - Incluye acceso a pantalla de clases por curso (`/bo/manage-courses/{courseId}/classes`).
   - Desde esa pantalla se pueden crear, editar y eliminar clases del curso.

3. **Gestionar clases**
   - Hub de cursos para abrir la gestion de clases sin pasar por la tabla de administracion.
   - Navega a `/bo/manage-courses/{courseId}/classes` para crear, editar o eliminar clases.

## Backend

### Endpoints

- `GET /api/backoffice/courses`
  - Devuelve todos los cursos (incluyendo no publicados).

- `POST /api/backoffice/courses`
  - Crea curso nuevo.
  - Genera `slug` automaticamente si no se envia.

- `PATCH /api/backoffice/courses/{course_id}`
  - Actualiza campos del curso (`title`, `category`, `progress`, `published`).

- `POST /api/backoffice/courses/{course_id}/classes`
  - Crea una clase asociada al curso.
  - Inserta en `classes` con `id_curso`, `nombre_clase`, `descripcion`, `url_video`.

- `GET /api/backoffice/courses/{course_id}/classes`
  - Lista clases asociadas al curso (puede devolver lista vacia).

- `PATCH /api/backoffice/courses/{course_id}/classes/{class_id}`
  - Actualiza datos de la clase (`nombre_clase`, `descripcion`, `url_video`).

- `DELETE /api/backoffice/courses/{course_id}/classes/{class_id}`
  - Elimina la clase asociada al curso.

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

- Archivo: `backend/db/migrations/20260401_el21_certificates_table.sql`
  - Crea tabla `certificates` para registrar certificados emitidos por alumno y curso.
