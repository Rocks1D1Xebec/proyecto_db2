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

## Tecnologias Previstas a Usar

### 1. Backend
- **Python:** Lenguaje principal de programacion para la logica del servidor.
- **Framework Web (FastAPI / Flask):** Para construir la API REST, gestionar rutas de autenticacion, listas y servir peticiones al frontend.

### 2. Frontend (Interfaz Web)
- **HTML5:** Estructura de las vistas y uso de la etiqueta semantica de audio para streaming.
- **CSS3:** Maquetacion, diseño visual moderno y adaptacion responsiva.
- **JavaScript (Vanilla JS):** Control de eventos del reproductor (play, pause, barra de progreso), reproduccion continua en segundo plano y comunicacion asincrona con el backend mediante API Fetch (AJAX) sin recargar la pagina.

### 3. Procesamiento Multimedia y Audio
- **yt-dlp:** Libreria de Python para la extraccion de metadatos y captura del stream de audio desde YouTube / YouTube Music.
- **FFmpeg:** Herramienta para la conversion, normalizacion y codificacion del audio a formato MP3 con bitrate optimizado.

### 4. Almacenamiento de Archivos (Object Storage)
- **Cloudflare R2:** Almacenamiento de objetos desacoplado en la nube para guardar los archivos MP3 (10 GB gratuitos).

### 5. Base de Datos Relacional
- **MySQL / PostgreSQL (Neon):** Motor de base de datos relacional para la persistencia de usuarios, credenciales, historial de logins, artistas, canciones, playlists e integridad referencial.

### 6. Despliegue e Infraestructura
- **Render:** Plataforma de alojamiento en la nube para el Web Service en produccion.

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

1. **`usuario` (Registro):** Cuentas de usuario registradas con credenciales protegidas y fecha de alta.
2. **`login` (Inicio de Sesion):** Control y auditoria de accesos de cada usuario (fecha de ingreso, IP y estado).
3. **`artista`:** Catalogo normalizado de artistas para evitar redundancia de texto.
4. **`cancion`:** Metadatos tecnicos de las canciones (titulo, duracion, id de youtube, formato, usuario que la subio y enlace a Cloudflare R2).
5. **`lista`:** Listas de reproduccion personalizadas creadas por los usuarios.
6. **`detalle_lista`:** Tabla asociativa que resuelve la relacion Muchos a Muchos (N:M) entre listas y canciones con restriccion para evitar duplicados.

---

## Meta para el Primer Avance
- Presentar el modelo de datos formal (diagrama relacional y script DDL `Lyra.sql`) debidamente normalizado con claves foraneas, restricciones de integridad y estructura para inicio de sesion y registro.
