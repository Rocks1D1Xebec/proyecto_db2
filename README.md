# Lyra 🎵 - Web de Música en la Nube
### Proyecto Base de Datos II (DB2)

## 📌 Descripción y Enfoque
- **Nombre del Proyecto:** Lyra
- **Materia:** Base de Datos II (DB2).
- **Concepto:** Plataforma web de música en la nube que permite a los usuarios gestionar su catálogo musical, reproducir canciones vía streaming y descargarlas en formato MP3.
- **Enfoque de la defensa:** La defensa estará fuertemente centrada en la base de datos (modelado, normalización, integridad referencial, transacciones, optimización y gestión), ya que es el núcleo temático de la materia.
- **Restricciones:** No hay restricciones sobre las tecnologías a utilizar (stack libre).

---

## 🛠️ Stack Tecnológico

- **Backend:** Python.
- **Procesamiento y Gestión de Audio:**
  - `yt-dlp`: Para la descarga y obtención de audio.
  - `FFmpeg`: Para la conversión, procesamiento y estandarización a archivos MP3.
- **Almacenamiento de Archivos (Object Storage):**
  - Posibilidad de usar [Cloudflare R2](https://www.cloudflare.com/products/r2/) para el almacenamiento de los archivos MP3 en la nube con cero costos de egress.
- **Despliegue Web:**
  - **Web Service:** [Render](https://render.com/)
- **Base de Datos (Por definir):**
  - Se mantiene en evaluación el uso de **[Neon](https://neon.tech/)** (PostgreSQL Serverless) o **[Cloudflare D1](https://developers.cloudflare.com/d1/)** (SQLite distribuido), analizando cuál ofrece mayores ventajas para las exigencias de DB2.

---

## 🎯 Meta para el Martes: Primer Avance
- Diseñar y presentar el modelo de datos para la base de datos requerido para el primer avance.
