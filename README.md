# Lyra 🎵 - Web de Música en la Nube
### Proyecto Base de Datos II (DB2)

## 📌 Descripción y Enfoque
- **Nombre del Proyecto:** Lyra
- **Materia:** Base de Datos II (DB2).
- **Concepto:** Plataforma web de música en la nube que permite a los usuarios gestionar su catálogo musical, reproducir canciones vía streaming y descargarlas en formato MP3.
- **Fuente de Audio Exclusiva:** La plataforma trabajará **únicamente con enlaces de YouTube y YouTube Music** (`youtube.com`, `music.youtube.com`, `youtu.be`). Esta delimitación asegura una fuente canónica única, evita inconsistencias de datos y previene que una misma canción se duplique por provenir de servicios externos distintos.
- **Enfoque de la defensa:** La defensa estará fuertemente centrada en la base de datos (modelado relacional, normalización, integridad referencial, transacciones, optimización con índices y gestión), ya que es el núcleo temático de la materia.
- **Restricciones:** No hay restricciones sobre las tecnologías a utilizar (stack libre).

---

## 🛠️ Stack Tecnológico Definido

- **Backend:** Python.
- **Procesamiento y Gestión de Audio:**
  - `yt-dlp`: Para la obtención, extracción de metadatos y descarga del flujo de audio.
  - `FFmpeg`: Para la conversión y estandarización a archivos MP3.
- **Almacenamiento de Archivos (Object Storage):**
  - **[Cloudflare R2](https://www.cloudflare.com/products/r2/):** Almacenamiento desacoplado para los archivos MP3 en la nube (10 GB gratis y 0 costos de egress).
- **Base de Datos Relacional:**
  - **[Neon](https://neon.tech/) (PostgreSQL Serverless):** Gestión de metadatos, integridad referencial, transacciones ACID y consultas avanzadas.
- **Despliegue Web:**
  - **Web Service:** [Render](https://render.com/)

---

## 🎵 Datos y Metadatos Extraídos con `yt-dlp`

Al procesar un enlace de YouTube o YouTube Music, la librería `yt-dlp` extrae la información técnica y musical que se persiste en la base de datos y en el almacenamiento:

| Dato Extraído (`yt-dlp`) | Tipo de Dato | Uso en la Base de Datos / Sistema |
| :--- | :--- | :--- |
| `id` | `VARCHAR(30)` | **ID único de YouTube** (ej. `dQw4w9WgXcQ`). Campo `UNIQUE` para deduplicación: si ya existe, no se vuelve a descargar. |
| `title` | `VARCHAR(250)` | Título oficial de la canción. |
| `artist` / `uploader` | `VARCHAR(150)` | Nombre del artista oficial (YouTube Music) o canal creador. Almacenado en la entidad normalizada `artista`. |
| `album` | `VARCHAR(200)` | Nombre del álbum discográfico (disponible al importar desde YouTube Music). |
| `duration` | `INTEGER` | Duración total de la canción expresada en **segundos** (facilita cálculos y formateo en la web). |
| `thumbnail` | `TEXT` (URL) | Enlace directo a la portada o miniatura oficial en alta resolución. |
| `filesize_approx` | `BIGINT` | Tamaño aproximado del archivo en bytes (para cálculo de uso de cuota y estadísticas). |
| `webpage_url` | `TEXT` (URL) | URL original canónica del video o pista. |
| **Stream de Audio** | Archivo `.mp3` | Audio convertido con `FFmpeg` y subido a Cloudflare R2, guardando su URL final (`r2_url`) en la BD. |

---

## 🗄️ Entidades Iniciales de la Base de Datos
Para el arranque del modelo relacional se definen las siguientes entidades base:
1. **`usuario`**: Cuentas con roles (`usuario`, `admin`) para control de acceso y auditoría.
2. **`artista`**: Normalización del autor o banda para evitar duplicación de texto.
3. **`cancion`**: Metadatos de audio extraídos por `yt-dlp`, referencia a R2 y deduplicación por `youtube_id`.
4. **`lista`**: Playlists creadas por los usuarios.
5. **`detalle_lista`**: Tabla intermedia que resuelve la relación Muchos a Muchos ($N:M$) entre listas y canciones con orden de reproducción.

---

## 🎯 Meta para el Martes: Primer Avance
- Diseñar y presentar el modelo de datos formal (diagrama relacional y script DDL `Lyra.sql`) debidamente normalizado (3FN) con índices y restricciones para la defensa.
