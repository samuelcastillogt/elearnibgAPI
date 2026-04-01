# Flujo de clases por alumno

Este documento cubre la implementacion de EL-13: registro de clases por curso, seguimiento por alumno y finalizacion con certificado.

## Estructura de datos

```mermaid
erDiagram
  courses ||--o{ classes : contiene
  courses ||--o{ course_student : asigna
  courses ||--o{ classes_student : rastrea
  courses ||--o{ certificates : certifica
  classes ||--o{ classes_student : progreso

  courses {
    bigint id PK
    text slug
    text title
    text category
    integer progress
  }

  classes {
    bigint id PK
    bigint id_curso FK
    text nombre_clase
    text descripcion
    text url_video
  }

  course_student {
    bigint id PK
    text id_alumno
    bigint id_curso FK
    boolean status
    text id_certificado
    timestamptz fecha_asignacion
    timestamptz fecha_finalizado
  }

  classes_student {
    bigint id PK
    bigint id_curso FK
    bigint id_clase FK
    text id_alumno
    integer time
    boolean status
  }

  certificates {
    bigint id PK
    text id_alumno
    bigint id_curso FK
    text id_certificacion
    timestamptz fecha_emision
  }
```

## Flujo funcional

```mermaid
sequenceDiagram
  participant UI as Frontend
  participant API as FastAPI
  participant DB as Supabase

  UI->>API: GET /api/courses/{course}/students/{uid}/progress
  API->>DB: Busca curso y clases
  API->>DB: Busca course_student por curso+alumno
  alt No existe course_student
    API->>DB: Crea course_student(status=false)
  end
  API->>DB: Busca classes_student del alumno
  alt Faltan registros
    API->>DB: Inserta filas faltantes (una por clase)
  end
  API-->>UI: Progreso consolidado + accion sugerida

  UI->>API: POST /api/courses/{course}/students/{uid}/classes/{classId}/complete
  API->>DB: Marca clase en status=true
  API->>DB: Recalcula pendientes
  alt Pendientes = 0
    API->>DB: Inserta certificado en certificates
    API->>DB: Actualiza course_student.status=true
    API->>DB: Genera y guarda id_certificado
  end
  API-->>UI: Progreso actualizado
```

## Endpoints nuevos

- `GET /api/courses/{course_ref}/students/{student_uid}/progress`
  - Crea registro de asignacion y detalle de clases si aun no existe.
  - Retorna clases completadas, pendientes, etiqueta de accion y certificado si aplica.
- `POST /api/courses/{course_ref}/students/{student_uid}/classes/{class_id}/complete`
  - Marca una clase como completada.
  - Recalcula estado del curso y genera certificado cuando ya no hay pendientes.

## Reglas de negocio implementadas

- Si el alumno entra al detalle de un curso por primera vez, se crea `course_student` con `status=false`.
- Se generan registros en `classes_student` por cada clase del curso para ese alumno.
- El avance del curso se calcula con base en `classes_student.status`.
- Cuando no quedan clases pendientes, `course_student.status` pasa a `true` y se guarda `id_certificado`.
- Al finalizar el curso, se crea un registro en `certificates` con `id_alumno` y `id_certificacion` unico.
- En frontend:
  - La pagina del curso abre un reproductor de YouTube con listado lateral de clases.
  - Se selecciona automaticamente la siguiente clase tomando como referencia la ultima clase completada.
  - Cada clase permite marcarse como completada manualmente.
  - Al terminar un video se marca la clase actual como completada (si estaba pendiente) y avanza a la siguiente.
  - Se muestra el codigo de certificado cuando el curso esta finalizado.
