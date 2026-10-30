# Proyecto Base de Datos II (DB2)

## 📌 Descripción y Enfoque
- **Materia:** Base de Datos II (DB2).
- **Enfoque de la defensa:** La defensa estará fuertemente centrada en la base de datos (modelado, normalización, integridad referencial, transacciones, optimización y gestión), ya que es el núcleo temático de la materia.
- **Restricciones:** No hay restricciones sobre las tecnologías a utilizar (stack libre).

---

## 🚀 Infraestructura y Despliegue
El proyecto debe estar desplegado en producción y accesible vía web:
- **Web Service:** [Render](https://render.com/)
- **Base de Datos:** [Neon](https://neon.tech/) (PostgreSQL Serverless) o [Cloudflare D1](https://developers.cloudflare.com/d1/) (SQLite distribuido)

---

## 🎯 Meta para el Martes: Primer Avance de Base de Datos
Para la primera entrega se requiere presentar:
1. **Diagrama Entidad-Relación (DER) / Modelo Relacional:** Tablas normalizadas (3FN) con llaves primarias (`PK`) y foráneas (`FK`).
2. **Script DDL inicial (`schema.sql`):** Creación de tablas, tipos de datos apropiados, restricciones (`NOT NULL`, `UNIQUE`, `CHECK`, `DEFAULT`).
3. **Población con datos de prueba (`seeds.sql`):** Registros simulados para validar relaciones y consultas clave.
4. **Justificación de conceptos de DB2:** Aplicación de índices, vistas, integridad transaccional y posibles triggers/procedimientos.

---

## 💡 Opciones de Ideas de Proyecto

### Opción 1: Web de Música en la Nube (Cloud Music Locker & Streamer(Tipo youtube music "gratis"))
*Permite a los usuarios subir su música a almacenamiento en la nube, organizarla en bibliotecas y playlists, reproducirla vía streaming y descargarla.*

- **Puntos clave del sistema:**
  - Carga y descarga de archivos de audio (almacenamiento en bucket de nube tipo Cloudflare R2 / S3 / Supabase Storage; metadatos y enlaces firmados persistidos en BD).
  - Extracción y gestión de metadatos (título, artista, álbum, año, duración, bitrate, género).
  - Creación de listas de reproducción personalizadas y compartidas.
  - Historial y métricas de descargas y reproducciones.

- **Diseño del Modelo en Base de Datos (DB2):**
  - `usuarios` (`id`, `nombre`, `email`, `password_hash`, `espacio_usado_mb`, `limite_mb`, `fecha_creacion`)
  - `artistas` (`id`, `nombre`, `biografia`, `pais`)
  - `albumes` (`id`, `titulo`, `artista_id`, `anio_lanzamiento`, `portada_url`)
  - `generos` (`id`, `nombre`)
  - `canciones` (`id`, `usuario_id`, `titulo`, `artista_id`, `album_id`, `genero_id`, `duracion_seg`, `archivo_url`, `peso_bytes`, `formato`, `fecha_subida`)
  - `playlists` (`id`, `usuario_id`, `nombre`, `descripcion`, `es_publica`, `fecha_creacion`)
  - `playlist_canciones` (`playlist_id`, `cancion_id`, `orden_reproduccion`, `agregado_en`) *(Relación N:M)*
  - `descargas_historial` (`id`, `usuario_id`, `cancion_id`, `fecha_descarga`, `ip_origen`)
  - `reproducciones_log` (`id`, `usuario_id`, `cancion_id`, `progreso_seg`, `fecha_reproduccion`)

- **Aspectos avanzados para defender en DB2:**
  - **Triggers:** Actualizar automáticamente el campo `espacio_usado_mb` en `usuarios` cada vez que se sube (`INSERT`) o elimina (`DELETE`) una canción.
  - **Índices:** Índices B-Tree en `(usuario_id, cancion_id)` e índices de búsqueda por texto en títulos de canciones y artistas.
  - **Vistas:** Vistas analíticas como `vista_top_canciones_mas_descargadas` o `vista_resumen_biblioteca_usuario`.
  - **Transacciones:** Garantizar atomicidad al reordenar listas o borrar listas completas con sus detalles.

---

### Opción 2: Asistente Personalizado (Personal AI Assistant & Hub de Productividad(Tipo Jarvis))
*Asistente personal que gestiona tareas, notas, recordatorios, hábitos y contextos de conversación, actuando como un centro neurálgico personal.*

- **Puntos clave del sistema:**
  - Gestión de conversaciones e interacciones con memoria contextual.
  - Panel de productividad: tareas por prioridad, recordatorios con fechas límite, etiquetas y estados (pendiente, en progreso, completado).
  - Almacenamiento de notas y contexto personalizado que el asistente consulta para responder.

- **Diseño del Modelo en Base de Datos (DB2):**
  - `usuarios` (`id`, `nombre`, `email`, `configuracion_json`, `fecha_registro`)
  - `conversaciones` (`id`, `usuario_id`, `titulo`, `tema`, `fecha_creacion`, `ultima_actividad`)
  - `mensajes` (`id`, `conversacion_id`, `rol`, `contenido`, `tokens_usados`, `fecha_envio`)
  - `categorias_etiquetas` (`id`, `usuario_id`, `nombre`, `color_hex`)
  - `tareas_recordatorios` (`id`, `usuario_id`, `titulo`, `descripcion`, `prioridad`, `estado`, `fecha_limite`, `completada_en`)
  - `tarea_etiquetas` (`tarea_id`, `etiqueta_id`) *(Relación N:M)*
  - `notas_conocimiento` (`id`, `usuario_id`, `titulo`, `contenido`, `fecha_actualizacion`)
  - `recordatorios_programados` (`id`, `tarea_id`, `fecha_notificacion`, `enviado`)

- **Aspectos avanzados para defender en DB2:**
  - **Integridad y Restricciones:** `CHECK` en niveles de prioridad (`BAJA`, `MEDIA`, `ALTA`, `URGENTE`) y estados válidos.
  - **Transacciones:** Creación transaccional de una tarea + asignación de etiquetas + registro de recordatorio simultáneo.
  - **Búsqueda eficiente:** Índices GIN o de texto completo para buscar palabras clave dentro del historial de mensajes y notas.
  - **Procedimientos almacenados:** Función para purgar mensajes antiguos o generar resúmenes periódicos de tareas vencidas.
