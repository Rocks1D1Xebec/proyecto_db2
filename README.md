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
| Despliegue / Servidor | Oracle Cloud (Linux) | Alojamiento y despliegue del servicio web y procesamiento en una instancia Compute Linux (OCI). |

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

---

## Justificaciones sobre Cambios en el Plan

### 1. Justificaciones de la Base de Datos
- **Modificación de tablas (Unificación de Usuario):** Se descartó la división inicial de tres tablas (`registro`, `login` y `usuario`) en favor de una única tabla **`usuario`** por las siguientes razones:
  - **Eliminación de redundancia y 3FN:** En el esquema previo, el campo `correo` estaba duplicado en dos tablas. En el modelo relacional, todos los atributos de una cuenta (`nombre`, `correo`, `contrasena`, `fecha_registro`, `ultimo_acceso`) dependen funcionalmente de la misma clave primaria (`id`), cumpliendo con la Tercera Forma Normal (3FN).
  - **Distinción entre Proceso y Entidad:** "Registrarse" e "Iniciar sesión" son acciones o transacciones del sistema, no entidades independientes. La entidad real es el usuario.

### 2. Justificaciones sobre Infraestructura y Despliegue (Migración de Render a Oracle Cloud)
- **Limitaciones identificadas en Render:** Inicialmente se consideró Render como plataforma PaaS para el alojamiento; sin embargo, presentó limitaciones críticas para los requisitos del sistema:
  - **Restricciones con FFmpeg y binarios del sistema:** Render impone limitaciones y complejidades para la instalación y configuración nativa de herramientas a nivel de sistema operativo como `FFmpeg` y sus códecs asociados, componentes indispensables para que `yt-dlp` realice la extracción, transcodificación y conversión de audio a MP3.
  - **Límites de tiempo (Timeouts) e inactividad:** Las plataformas PaaS como Render imponen tiempos máximos de ejecución estrictos para solicitudes y suspenden instancias por inactividad ("spin-down"), lo que interrumpe o aborta descargas y transcodificaciones de audio en segundo plano.
  - **Restricciones de memoria y CPU:** El procesamiento multimedia demanda recursos de cómputo que en entornos gratuitos o compartidos de PaaS provocan cuellos de botella y fallos por agotamiento de memoria.
- **Decisión técnica (Instancia Compute en Oracle Cloud con Linux):** Ante estas restricciones, se tomó la decisión de utilizar una **instancia virtual en Oracle Cloud Infrastructure (OCI)** con una **distribución de Linux** (ej. Ubuntu Server):
  - **Control total a nivel de sistema operativo (Acceso Root):** Permite instalar y configurar de forma nativa `FFmpeg`, librerías multimedia y `yt-dlp` mediante el gestor de paquetes de Linux (`apt`), garantizando total compatibilidad.
  - **Recursos dedicados y rendimiento:** Provisión de CPU y memoria RAM dedicada para procesar conversiones pesadas de audio sin caídas ni bloqueos.
  - **Ejecución continua de procesos en segundo plano:** Posibilidad de gestionar demonios, workers y tareas asíncronas de manera ininterrumpida sin sufrir suspensiones automáticas ni caídas por límites de tiempo HTTP.
  - **Gestión eficiente de archivos temporales:** Permite almacenar y manipular temporalmente las pistas en disco local durante la fase de descarga y compresión antes de ser enviadas a Cloudflare R2.
  - **Alojamiento persistente de credenciales:** Facilita el almacenamiento persistente de archivos de configuración y autenticación que `yt-dlp` necesita en disco.

### 3. Justificación sobre la Gestión de Cookies de YouTube (`cookies.txt`)
- **Exclusión de las cookies de la Base de Datos:** Se analizó si era necesario crear una tabla relacional para persistir los datos de sesión/cookies de YouTube, determinándose **no incluirlas** en la base de datos por las siguientes razones:
  - **Separación de responsabilidades:** La base de datos modela exclusivamente las entidades y reglas del negocio (`usuario`, `cancion`, `artista`, `lista`). Las cookies de YouTube constituyen un parámetro técnico de infraestructura del backend y de `yt-dlp`.
  - **Requisito nativo de `yt-dlp`:** La librería espera directamente un archivo en formato estándar Netscape (`cookies.txt`). Guardarlas en una tabla implicaría una sobrecarga innecesaria de consultas SQL y reescritura constante en disco en cada descarga.
  - **Seguridad y confidencialidad:** Mantener tokens de sesión de un servicio externo fuera de las tablas transaccionales reduce la superficie de exposición y facilita la rotación de credenciales.
- **Implementación en la Instancia de Oracle Cloud (Linux):**
  - Aprovechando el sistema de archivos persistente de la instancia Compute en Oracle Cloud, el archivo `cookies.txt` se subirá directamente al servidor en un directorio protegido y con permisos restringidos a nivel de sistema operativo (`chmod 600`).
  - El backend en Python apuntará a dicha ruta mediante la directiva `'cookiefile': '/ruta/cookies.txt'` en `YoutubeDL`, permitiendo autenticar las peticiones y evitar los bloqueos por detección de bots ("Sign in to confirm you're not a bot") que YouTube aplica a IPs de centros de datos.

