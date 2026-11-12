# Lyra - Web de Musica en la Nube
### Proyecto Base de Datos II (DB2)

## Descripcion y Enfoque
- **Nombre del Proyecto:** Lyra
- **Materia:** Base de Datos II (DB2).
- **Concepto:** Plataforma web de musica en la nube que permite a los usuarios gestionar su catalogo musical, reproducir canciones via streaming en segundo plano y descargarlas en formato MP3.
- **Fuente de Audio Exclusiva:** La plataforma trabajara unicamente con enlaces de YouTube y YouTube Music (`youtube.com`, `music.youtube.com`, `youtu.be`). Esta delimitacion asegura una fuente canonica unica, evita inconsistencias de datos y previene que una misma cancion se duplique por provenir de servicios externos distintos.
- **Enfoque de la defensa:** La defensa estara fuertemente centrada en la base de datos (modelado relacional, normalizacion, integridad referencial, transacciones, optimizacion con indices y gestion), ya que es el nucleo tematico de la materia.
- **Restricciones:** No hay restricciones sobre las tecnologias a utilizar (stack libre).

---

## Tecnologías

| Área | Tecnología | Uso |
| :--- | :--- | :--- |
| Frontend | HTML5, CSS3 y JavaScript | Estructura, diseño e interacción de las páginas y control del reproductor. |
| Backend | Python | Implementación de la lógica del servidor. |
| Framework del backend | FastAPI / Flask | Organización de la aplicación, rutas, validaciones y acceso a datos. |
| Base de datos | PostgreSQL / MySQL | Almacenamiento y gestión de la información relacional. |
| Procesamiento de audio | yt-dlp y FFmpeg | Extracción de metadatos desde YouTube y conversión a MP3. |
| Almacenamiento de archivos | Cloudflare R2 | Almacenamiento desacoplado en la nube para los archivos de audio MP3. |
| Despliegue | Render | Alojamiento y despliegue del servicio web en producción. |

---

## Datos y Metadatos Extraidos con yt-dlp

Al procesar un enlace de YouTube o YouTube Music, la libreria `yt-dlp` extrae la informacion tecnica y musical que se persiste en la base de datos y en el almacenamiento:

| Dato Extraido (`yt-dlp`) | Tipo de Dato | Uso en la Base de Datos / Sistema |
| :--- | :--- | :--- |
| `id` | `VARCHAR(50)` | ID unico de YouTube (ej. `dQw4w9WgXcQ`). Campo `UNIQUE` para deduplicacion: si ya existe, no se vuelve a descargar. |
| `title` | `VARCHAR(100)` | Titulo oficial de la cancion. |
| `artist` / `uploader` | `VARCHAR(100)` | Nombre del artista oficial o canal creador. Almacenado en la entidad normalizada `artista`. |
| `duration` | `INT UNSIGNED` | Duracion total de la cancion expresada en segundos (facilita calculos y formateo en la web). |
| `link_r2` | `TEXT` | Enlace publico o firmado al archivo de audio alojado en Cloudflare R2. |
| `formato` | `VARCHAR(10)` | Formato de codificacion del archivo (ej. `mp3`). |

---

## Entidades de la Base de Datos

1. **`usuario`:** Cuentas de usuario que centralizan credenciales (correo, contraseña), perfil (nombre) y auditoría (fecha de registro y último acceso).
2. **`artista`:** Catálogo normalizado de artistas para evitar redundancia de texto.
3. **`cancion`:** Metadatos técnicos de las canciones (título, duración, ID de YouTube, formato, usuario que la subió y enlace a Cloudflare R2).
4. **`lista`:** Listas de reproducción personalizadas creadas por los usuarios.
5. **`detalle_lista`:** Tabla asociativa que resuelve la relación Muchos a Muchos (N:M) entre listas y canciones con restricción para evitar duplicados.
6. **`me_gusta`:** Registro de canciones marcadas como favoritas por cada usuario (relación N:M).

---

## Meta para el Primer Avance
- Presentar el modelo de datos formal (diagrama relacional y script DDL `Lyra.sql`) debidamente normalizado con claves foráneas, restricciones de integridad y estructura optimizada para usuarios y listas.

## Justificaciones de la Base de Datos
1. **Modificación de tablas (Unificación de Usuario):** Se descartó la división inicial de tres tablas (`registro`, `login` y `usuario`) en favor de una única tabla **`usuario`** por las siguientes razones:
   - **Eliminación de redundancia y 3FN:** En el esquema previo, el campo `correo` estaba duplicado en dos tablas. En el modelo relacional, todos los atributos de una cuenta (`nombre`, `correo`, `contrasena`, `fecha_registro`, `ultimo_acceso`) dependen funcionalmente de la misma clave primaria (`id`), cumpliendo con la Tercera Forma Normal (3FN).
   - **Distinción entre Proceso y Entidad:** "Registrarse" e "Iniciar sesión" son acciones o transacciones del sistema, no entidades independientes. La entidad real es el usuario.