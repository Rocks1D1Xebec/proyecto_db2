import os
import json
import socket
import shutil
import asyncio
import tempfile
import subprocess
import pymysql
from pymysql.cursors import DictCursor
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
import uvicorn
import boto3
from botocore.config import Config
import yt_dlp

# configuracion mysql
servidor = "localhost"
usuario = "********"
clave = "********"
base_datos = "lyra"
puerto = 3306

# configuracion r2
r2_bucket = "********"
r2_endpoint = "https://********************************.r2.cloudflarestorage.com"
r2_access_key = "********************************"
r2_secret_key = "****************************************************************"

app = FastAPI()

def conectar():
    # conexion a mysql
    try:
        conexion = pymysql.connect(
            host=servidor,
            user=usuario,
            password=clave,
            database=base_datos,
            port=puerto,
            charset="utf8mb4",
            cursorclass=DictCursor,
            connect_timeout=3,
            autocommit=True
        )
        return conexion
    except Exception as error:
        print("Error de conexion MySQL:", error)
        return None

def conectar_r2():
    # cliente r2
    try:
        cliente = boto3.client(
            "s3",
            endpoint_url=r2_endpoint,
            aws_access_key_id=r2_access_key,
            aws_secret_access_key=r2_secret_key,
            config=Config(signature_version="s3v4"),
            region_name="auto"
        )
        return cliente
    except Exception as error:
        print("Error de conexion Cloudflare R2:", error)
        return None

def subir_a_r2(ruta_archivo_local, nombre_destino):
    # sube archivo a r2
    cliente = conectar_r2()
    if not cliente:
        return None
    try:
        cliente.upload_file(
            ruta_archivo_local,
            r2_bucket,
            nombre_destino,
            ExtraArgs={"ContentType": "audio/mpeg"}
        )
        url_audio = cliente.generate_presigned_url(
            "get_object",
            Params={"Bucket": r2_bucket, "Key": nombre_destino},
            ExpiresIn=604800
        )
        return url_audio
    except Exception as error:
        print("Error al subir archivo a R2:", error)
        return None

def proxy_socks5_activo():
    # verifica si el tunel socks5 esta activo en el puerto 10808
    try:
        s = socket.create_connection(("127.0.0.1", 10808), timeout=0.5)
        s.close()
        return True
    except Exception:
        return False

def descargar_musica_youtube(enlace):
    # descarga audio con yt-dlp
    carpeta_temp = tempfile.mkdtemp()
    plantilla = os.path.join(carpeta_temp, "%(id)s.%(ext)s")
    ruta_cookies = os.path.join(os.path.dirname(__file__), "cookies.txt")

    opciones = {
        "format": "bestaudio/best",
        "outtmpl": plantilla,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "js_runtimes": {"deno": {"path": "/usr/local/bin/deno"}, "node": {}},
        "remote_components": ["ejs:github"],
        "socket_timeout": 10,
        "retries": 2,
        "quiet": True,
        "no_warnings": True,
    }

    if proxy_socks5_activo():
        opciones["proxy"] = "socks5://127.0.0.1:10808"
    elif os.path.exists(ruta_cookies):
        cookie_temp = os.path.join(carpeta_temp, "cookies_run.txt")
        shutil.copy2(ruta_cookies, cookie_temp)
        opciones["cookiefile"] = cookie_temp

    try:
        with yt_dlp.YoutubeDL(opciones) as ydl:
            info = ydl.extract_info(enlace, download=True)
            id_youtube = info.get("id")
            titulo = info.get("title", f"Cancion ({id_youtube})")
            artista = info.get("uploader") or info.get("channel") or info.get("artist") or "Artista Desconocido"
            duracion = int(info.get("duration", 0))

            ruta_mp3 = os.path.join(carpeta_temp, f"{id_youtube}.mp3")
            if not os.path.exists(ruta_mp3):
                for archivo in os.listdir(carpeta_temp):
                    if archivo.startswith(id_youtube):
                        ruta_mp3 = os.path.join(carpeta_temp, archivo)
                        break

            return {
                "id_youtube": id_youtube,
                "titulo": titulo,
                "artista": artista,
                "duracion": duracion,
                "ruta_archivo": ruta_mp3,
                "carpeta_temp": carpeta_temp
            }
    except Exception as error:
        print("Error en descargar_musica_youtube:", error)
        return None

def iniciar_sesion(correo, contraseña):
    # buscar usuario
    conexion = conectar()
    if not conexion:
        return None
    try:
        cursor = conexion.cursor()
        sql = "SELECT id, nombre, correo, fecha_registro FROM usuario WHERE correo = %s AND contraseña = %s"
        cursor.execute(sql, (correo, contraseña))
        usuario_encontrado = cursor.fetchone()
        cursor.close()
        conexion.close()
        return usuario_encontrado
    except Exception as error:
        print("Error en iniciar_sesion:", error)
        return None

def registrar_usuario(nombre, correo, contraseña):
    # registrar usuario
    conexion = conectar()
    if not conexion:
        return None
    try:
        cursor = conexion.cursor()
        sql = "INSERT INTO usuario (nombre, correo, contraseña) VALUES (%s, %s, %s)"
        cursor.execute(sql, (nombre, correo, contraseña))
        nuevo_id = cursor.lastrowid
        cursor.close()
        conexion.close()
        return nuevo_id
    except Exception as error:
        print("Error en registrar_usuario:", error)
        return None

def ver_catalogo():
    # vista de catalogo
    conexion = conectar()
    if not conexion:
        return None
    try:
        cursor = conexion.cursor()
        sql = "SELECT * FROM vw_catalogo_canciones ORDER BY fecha_subida DESC"
        cursor.execute(sql)
        resultado = cursor.fetchall()
        cursor.close()
        conexion.close()
        return resultado
    except Exception as error:
        print("Error en ver_catalogo:", error)
        return None

def ver_populares(limite=10):
    # canciones populares
    conexion = conectar()
    if not conexion:
        return None
    try:
        cursor = conexion.cursor()
        sql = "SELECT * FROM vw_canciones_populares LIMIT %s"
        cursor.execute(sql, (limite,))
        resultado = cursor.fetchall()
        cursor.close()
        conexion.close()
        return resultado
    except Exception as error:
        print("Error en ver_populares:", error)
        return None

def ejecutar_sp_subir_cancion(titulo, id_youtube, artista, id_usuario, duracion, link_r2):
    # procedimiento sp_subir_cancion
    conexion = conectar()
    if not conexion:
        return None
    try:
        cursor = conexion.cursor()
        try:
            cursor.callproc("sp_subir_cancion", (titulo, id_youtube, artista, id_usuario, duracion, link_r2))
        except pymysql.err.IntegrityError as ie:
            if ie.args and ie.args[0] == 1062:
                cursor.execute("UPDATE cancion SET link_r2 = %s WHERE id_youtube = %s", (link_r2, id_youtube))
            else:
                raise
        cursor.close()
        conexion.close()
        return True
    except Exception as error:
        print("Error en ejecutar_sp_subir_cancion:", error)
        return None

def formatear_duracion(segundos):
    # formato mm:ss
    try:
        s = int(segundos or 0)
        m = s // 60
        sec = s % 60
        return f"{m}:{sec:02d}"
    except Exception:
        return "0:00"

def alternar_me_gusta(id_usuario, id_cancion):
    # alternar like
    conexion = conectar()
    if not conexion:
        return None
    try:
        cursor = conexion.cursor()
        cursor.execute("SELECT id FROM me_gusta WHERE id_usuario = %s AND id_cancion = %s", (id_usuario, id_cancion))
        existe = cursor.fetchone()
        if existe:
            cursor.execute("DELETE FROM me_gusta WHERE id_usuario = %s AND id_cancion = %s", (id_usuario, id_cancion))
            le_gusta = False
        else:
            cursor.execute("INSERT INTO me_gusta (id_usuario, id_cancion) VALUES (%s, %s)", (id_usuario, id_cancion))
            le_gusta = True
        cursor.close()
        conexion.close()
        return le_gusta
    except Exception as error:
        print("Error en alternar_me_gusta:", error)
        return None

def obtener_ids_me_gusta_usuario(id_usuario):
    # ids de canciones con like
    conexion = conectar()
    if not conexion:
        return set()
    try:
        cursor = conexion.cursor()
        cursor.execute("SELECT id_cancion FROM me_gusta WHERE id_usuario = %s", (id_usuario,))
        filas = cursor.fetchall()
        cursor.close()
        conexion.close()
        return {f["id_cancion"] for f in filas}
    except Exception as error:
        print("Error en obtener_ids_me_gusta_usuario:", error)
        return set()

def dar_me_gusta(id_usuario, id_cancion):
    return alternar_me_gusta(id_usuario, id_cancion)

def ver_listas_usuario(id_usuario):
    # listas del usuario
    conexion = conectar()
    if not conexion:
        return None
    try:
        cursor = conexion.cursor()
        sql = """
            SELECT l.id, l.nombre, COUNT(d.id) AS total_canciones 
            FROM lista l
            LEFT JOIN detalle_lista d ON l.id = d.id_lista
            WHERE l.id_usuario = %s
            GROUP BY l.id, l.nombre
            ORDER BY l.id DESC
        """
        cursor.execute(sql, (id_usuario,))
        resultado = cursor.fetchall()
        cursor.close()
        conexion.close()
        return resultado
    except Exception as error:
        print("Error en ver_listas_usuario:", error)
        return None

def obtener_cancion_por_id(id_cancion):
    # cancion por id
    conexion = conectar()
    if not conexion:
        return None
    try:
        cursor = conexion.cursor()
        sql = """
            SELECT c.id AS id_cancion, c.titulo, a.nombre AS artista, c.duracion, c.link_r2
            FROM cancion c
            INNER JOIN artista a ON c.id_artista = a.id
            WHERE c.id = %s
        """
        cursor.execute(sql, (id_cancion,))
        resultado = cursor.fetchone()
        cursor.close()
        conexion.close()
        return resultado
    except Exception as error:
        print("Error en obtener_cancion_por_id:", error)
        return None

def ver_canciones_lista(id_lista):
    # canciones de la lista
    conexion = conectar()
    if not conexion:
        return None
    try:
        cursor = conexion.cursor()
        sql = """
            SELECT c.id AS id_cancion, c.titulo, a.nombre AS artista, c.duracion, c.id_youtube, c.link_r2, d.id AS id_detalle
            FROM detalle_lista d
            INNER JOIN cancion c ON d.id_cancion = c.id
            INNER JOIN artista a ON c.id_artista = a.id
            WHERE d.id_lista = %s
            ORDER BY d.id ASC
        """
        cursor.execute(sql, (id_lista,))
        resultado = cursor.fetchall()
        cursor.close()
        conexion.close()
        return resultado
    except Exception as error:
        print("Error en ver_canciones_lista:", error)
        return None

def crear_lista(id_usuario, nombre):
    # procedimiento sp_crear_lista
    conexion = conectar()
    if not conexion:
        return None
    try:
        cursor = conexion.cursor()
        cursor.callproc("sp_crear_lista", (id_usuario, nombre))
        res = cursor.fetchone()
        nuevo_id = res["id"] if res and "id" in res else cursor.lastrowid
        cursor.close()
        conexion.close()
        return nuevo_id
    except Exception as error:
        print("Error en crear_lista:", error)
        return None

def eliminar_lista(id_lista, id_usuario):
    # procedimiento sp_eliminar_lista
    conexion = conectar()
    if not conexion:
        return False
    try:
        cursor = conexion.cursor()
        cursor.callproc("sp_eliminar_lista", (id_lista, id_usuario))
        cursor.close()
        conexion.close()
        return True
    except Exception as error:
        print("Error en eliminar_lista:", error)
        return False

def ver_canciones_me_gusta(id_usuario):
    # canciones favoritas
    conexion = conectar()
    if not conexion:
        return None
    try:
        cursor = conexion.cursor()
        sql = """
            SELECT c.id AS id_cancion, c.titulo, a.nombre AS artista, c.duracion, c.id_youtube, c.link_r2, m.fecha_agregado
            FROM me_gusta m
            INNER JOIN cancion c ON m.id_cancion = c.id
            INNER JOIN artista a ON c.id_artista = a.id
            WHERE m.id_usuario = %s
            ORDER BY m.fecha_agregado DESC
        """
        cursor.execute(sql, (id_usuario,))
        resultado = cursor.fetchall()
        cursor.close()
        conexion.close()
        return resultado
    except Exception as error:
        print("Error en ver_canciones_me_gusta:", error)
        return None

def eliminar_cancion_de_lista(id_lista, id_cancion):
    # procedimiento sp_eliminar_cancion_lista
    conexion = conectar()
    if not conexion:
        return False
    try:
        cursor = conexion.cursor()
        cursor.callproc("sp_eliminar_cancion_lista", (id_lista, id_cancion))
        cursor.close()
        conexion.close()
        return True
    except Exception as error:
        print("Error en eliminar_cancion_de_lista:", error)
        return False

def agregar_cancion_a_lista(id_lista, id_cancion):
    # procedimiento sp_agregar_cancion_lista
    conexion = conectar()
    if not conexion:
        return False
    try:
        cursor = conexion.cursor()
        cursor.callproc("sp_agregar_cancion_lista", (id_lista, id_cancion))
        cursor.close()
        conexion.close()
        return True
    except Exception as error:
        print("Error en agregar_cancion_a_lista:", error)
        return False

def generar_tarjeta_cancion(c, posicion=None, es_ranking=False, mostrar_eliminar=False, id_lista=None, indice=0, tiene_like=False):
    # tarjeta de cancion
    titulo = c.get("titulo") or "Sin titulo"
    artista = c.get("artista") or "Desconocido"
    duracion_txt = formatear_duracion(c.get("duracion"))
    id_cancion = c.get("id_cancion") or 0
    total_likes = c.get("total_me_gusta")

    badge_html = ""
    if es_ranking and posicion is not None:
        badge_html = f'<div class="music-meta-tags"><span class="badge badge-top">Top #{posicion} ({total_likes or 0} likes)</span></div>'
    elif total_likes is not None and total_likes > 0:
        badge_html = f'<div class="music-meta-tags"><span class="badge badge-top">{total_likes} likes</span></div>'

    boton_eliminar_html = ""
    if mostrar_eliminar and id_lista is not None:
        boton_eliminar_html = f"""
        <button type="button" class="btn-trash" title="Eliminar de esta lista" onclick="eliminarDeLista('{id_lista}', {id_cancion})">🗑</button>
        """

    icono_like = "❤️" if tiene_like else "♡"
    clase_like = "btn-like-active" if tiene_like else ""
    title_like = "Quitar de favoritos" if tiene_like else "Añadir a favoritos"

    return f"""
    <div class="music-track-card" data-id="{id_cancion}">
        <div class="music-thumb-box">
            <img src="https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?auto=format&fit=crop&w=400&q=80" alt="Cover" loading="lazy">
        </div>
        <div class="music-track-info">
            <div class="music-track-title" title="{titulo}">{titulo}</div>
            <div class="music-track-artist">👤 <span>{artista}</span> • {duracion_txt}</div>
            {badge_html}
            <div class="music-card-actions">
                <div class="music-actions-bar">
                    <div class="btn-group">
                        <button type="button" class="btn-action btn-escuchar" onclick="reproducirIndice({indice})">▶ Escuchar</button>
                        <button type="button" class="btn-action" title="Añadir a lista" onclick="agregarALista({id_cancion})">+</button>
                        <button type="button" class="btn-action btn-like {clase_like}" title="{title_like}" onclick="alternarMeGusta(event, {id_cancion})">{icono_like}</button>
                    </div>
                    {boton_eliminar_html}
                </div>
            </div>
        </div>
    </div>
    """

# rutas
@app.get("/lyra.css", response_class=Response)
def ruta_css():
    ruta = os.path.join(os.path.dirname(__file__), "lyra.css")
    with open(ruta, "r", encoding="utf-8") as f:
        return Response(content=f.read(), media_type="text/css")

@app.get("/", response_class=HTMLResponse)
@app.get("/catalogo", response_class=HTMLResponse)
def ruta_catalogo(request: Request, u: int = None):
    # catalogo general
    id_usuario = resolver_id_usuario(request, u)
    canciones = ver_catalogo() or []
    mis_likes = obtener_ids_me_gusta_usuario(id_usuario)
    tarjetas = ""
    cola = []
    for idx, c in enumerate(canciones):
        tiene_lk = c["id_cancion"] in mis_likes
        tarjetas += generar_tarjeta_cancion(c, indice=idx, tiene_like=tiene_lk)
        cola.append({"url": c.get("link_r2") or "", "titulo": c.get("titulo") or "Sin título", "artista": c.get("artista") or "Desconocido"})
    if not tarjetas:
        tarjetas = "<p style='color: var(--text-dim); padding: 20px;'>No hay canciones en el catálogo todavía.</p>"

    ruta_html = os.path.join(os.path.dirname(__file__), "catalogo.html")
    with open(ruta_html, "r", encoding="utf-8") as archivo:
        contenido = archivo.read()
    contenido = contenido.replace("<!-- TARJETAS_CANCIONES -->", tarjetas)
    contenido = contenido.replace("/* COLA_JSON */ []", json.dumps(cola)).replace("<!-- COLA_JSON -->", json.dumps(cola))
    return contenido

@app.get("/populares", response_class=HTMLResponse)
def ruta_populares(request: Request, u: int = None):
    # ranking populares
    id_usuario = resolver_id_usuario(request, u)
    populares = ver_populares() or []
    mis_likes = obtener_ids_me_gusta_usuario(id_usuario)
    tarjetas = ""
    cola = []
    for idx, c in enumerate(populares):
        tiene_lk = c["id_cancion"] in mis_likes
        tarjetas += generar_tarjeta_cancion(c, posicion=idx+1, es_ranking=True, indice=idx, tiene_like=tiene_lk)
        cola.append({"url": c.get("link_r2") or "", "titulo": c.get("titulo") or "Sin título", "artista": c.get("artista") or "Desconocido"})
    if not tarjetas:
        tarjetas = "<p style='color: var(--text-dim); padding: 20px;'>Aún no hay canciones con votos en el ranking.</p>"

    ruta_html = os.path.join(os.path.dirname(__file__), "populares.html")
    with open(ruta_html, "r", encoding="utf-8") as archivo:
        contenido = archivo.read()
    contenido = contenido.replace("<!-- TARJETAS_CANCIONES -->", tarjetas)
    contenido = contenido.replace("/* COLA_JSON */ []", json.dumps(cola)).replace("<!-- COLA_JSON -->", json.dumps(cola))
    return contenido

def obtener_nombre_lista(id_lista):
    # nombre de lista
    conexion = conectar()
    if not conexion:
        return "Lista"
    try:
        cursor = conexion.cursor()
        cursor.execute("SELECT nombre FROM lista WHERE id = %s", (id_lista,))
        row = cursor.fetchone()
        cursor.close()
        conexion.close()
        return row["nombre"] if row else "Lista"
    except Exception as error:
        print("Error en obtener_nombre_lista:", error)
        return "Lista"

def resolver_id_usuario(request: Request, u: int = None) -> int:
    # id de usuario activo
    if u and u > 0:
        return u
    cookie_u = request.cookies.get("usuario_id")
    if cookie_u and cookie_u.isdigit() and int(cookie_u) > 0:
        return int(cookie_u)
    return 1

@app.get("/listas", response_class=HTMLResponse)
def ruta_listas(request: Request, u: int = None):
    # listas del usuario
    id_usuario = resolver_id_usuario(request, u)

    favoritas = ver_canciones_me_gusta(id_usuario) or []
    total_mg = len(favoritas)

    tarjetas_listas = f"""
    <div class="playlist-card-wrapper">
        <a href="/playlist?id=megusta&u={id_usuario}" class="playlist-card playlist-card-favorites">
            <div class="playlist-cover-box playlist-cover-favorites">
                <img src="https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?auto=format&fit=crop&w=400&q=80" alt="Me gusta">
                <div class="playlist-cover-badge">❤️</div>
            </div>
            <div class="playlist-card-body">
                <div class="playlist-card-title">Canciones que te gustan</div>
                <div class="playlist-card-sub">{total_mg} canciones • Lista automática</div>
            </div>
        </a>
    </div>
    """

    listas = ver_listas_usuario(id_usuario) or []
    for l in listas:
        id_l = l.get("id") or l.get("id_lista")
        nom = l.get("nombre") or "Sin nombre"
        nom_esc = nom.replace("'", "\\'")
        total = l.get("total_canciones") or 0
        tarjetas_listas += f"""
        <div class="playlist-card-wrapper">
            <a href="/playlist?id={id_l}&u={id_usuario}" class="playlist-card">
                <div class="playlist-cover-box">
                    <img src="https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?auto=format&fit=crop&w=400&q=80" alt="Lista">
                    <div class="playlist-cover-badge">🎵</div>
                </div>
                <div class="playlist-card-body playlist-card-body-padded">
                    <div class="playlist-card-title">{nom}</div>
                    <div class="playlist-card-sub">{total} canciones • Lista personalizada</div>
                </div>
            </a>
            <button type="button" class="btn-delete-playlist" onclick="abrirModalEliminarLista(event, {id_l}, '{nom_esc}')" title="Eliminar lista '{nom_esc}'">
                🗑️
            </button>
        </div>
        """

    ruta_html = os.path.join(os.path.dirname(__file__), "listas.html")
    with open(ruta_html, "r", encoding="utf-8") as archivo:
        contenido = archivo.read()
    return contenido.replace("<!-- TARJETAS_LISTAS -->", tarjetas_listas)

@app.get("/playlist", response_class=HTMLResponse)
@app.get("/lista", response_class=HTMLResponse)
def ruta_detalle_playlist(request: Request, id: str = "megusta", u: int = None):
    # canciones de la playlist
    id_usuario = resolver_id_usuario(request, u)
    boton_eliminar_html = ""
    if str(id).lower() == "megusta" or str(id) == "0":
        nombre_lista = "❤️ Canciones que te gustan"
        canciones = ver_canciones_me_gusta(id_usuario) or []
    else:
        try:
            id_int = int(id)
            nom_actual = obtener_nombre_lista(id_int)
            nombre_lista = f"📁 {nom_actual}"
            nom_limpio = nom_actual.replace("'", "\\'")
            boton_eliminar_html = f'<button type="button" class="btn-danger-outline" onclick="abrirModalEliminarListaActual({id_int}, \'{nom_limpio}\')">🗑️ Eliminar Lista</button>'
            canciones = ver_canciones_lista(id_int) or []
        except Exception:
            nombre_lista = "Lista de Reproducción"
            canciones = []

    tarjetas = ""
    cola = []
    mis_likes = obtener_ids_me_gusta_usuario(id_usuario)
    for idx, c in enumerate(canciones):
        tiene_lk = c["id_cancion"] in mis_likes
        tarjetas += generar_tarjeta_cancion(c, mostrar_eliminar=True, id_lista=id, indice=idx, tiene_like=tiene_lk)
        cola.append({"url": c.get("link_r2") or "", "titulo": c.get("titulo") or "Sin título", "artista": c.get("artista") or "Desconocido"})
    if not tarjetas:
        tarjetas = "<p style='color: var(--text-dim); padding: 25px;'>Esta lista aún no tiene canciones agregadas.</p>"

    total = len(canciones)
    ruta_html = os.path.join(os.path.dirname(__file__), "playlist.html")
    with open(ruta_html, "r", encoding="utf-8") as archivo:
        contenido = archivo.read()

    contenido = contenido.replace("<!-- TITULO_LISTA -->", nombre_lista)
    contenido = contenido.replace("<!-- TOTAL_CANCIONES -->", f"{total} canciones")
    contenido = contenido.replace("<!-- BOTON_ELIMINAR_LISTA -->", boton_eliminar_html)
    contenido = contenido.replace("<!-- TARJETAS_CANCIONES -->", tarjetas)
    contenido = contenido.replace("/* COLA_JSON */ []", json.dumps(cola)).replace("<!-- COLA_JSON -->", json.dumps(cola))
    return contenido

@app.get("/subir", response_class=HTMLResponse)
def ruta_subir():
    # subir cancion
    ruta_html = os.path.join(os.path.dirname(__file__), "subir.html")
    with open(ruta_html, "r", encoding="utf-8") as archivo:
        return archivo.read()

@app.get("/agregar-a-lista", response_class=HTMLResponse)
def ruta_agregar_a_lista(request: Request, id_cancion: int = None, u: int = None):
    # agregar a lista
    id_usuario = resolver_id_usuario(request, u)
    cancion = obtener_cancion_por_id(id_cancion) if id_cancion else None
    listas = ver_listas_usuario(id_usuario) or []
    
    if cancion:
        titulo = cancion.get("titulo") or "Canción"
        artista = cancion.get("artista") or "Desconocido"
        duracion = formatear_duracion(cancion.get('duracion', 0))
        id_c = cancion.get("id_cancion")
        bloque_cancion = f"""
        <div class="add-selected-track-card">
            <div class="add-track-icon">🎵</div>
            <div>
                <span class="badge badge-top add-track-badge">Canción seleccionada</span>
                <div class="add-track-title">{titulo}</div>
                <div class="add-track-artist">👤 {artista} • {duracion}</div>
            </div>
            <input type="hidden" id="id-cancion-seleccionada" value="{id_c}">
        </div>
        """
    else:
        todas = ver_catalogo() or []
        opciones_c = "".join([f'<option value="{c["id_cancion"]}">{c["titulo"]} - {c["artista"]}</option>' for c in todas])
        bloque_cancion = f"""
        <div class="add-select-wrapper">
            <label class="add-select-label">Elige la canción que deseas añadir:</label>
            <select id="id-cancion-seleccionada" class="form-input add-select-input">
                {opciones_c}
            </select>
        </div>
        """

    items_listas = ""
    for l in listas:
        id_l = l.get("id") or l.get("id_lista")
        nom_l = l.get("nombre") or "Sin nombre"
        tot_l = l.get("total_canciones") or 0
        items_listas += f"""
        <div class="add-playlist-select-item">
            <div class="add-playlist-item-left">
                <div class="add-playlist-folder-icon">📁</div>
                <div>
                    <div class="add-playlist-name">{nom_l}</div>
                    <div class="add-playlist-count">{tot_l} canciones</div>
                </div>
            </div>
            <button type="button" class="btn-submit add-playlist-btn-submit" onclick="agregarAEstaLista({id_l}, '{nom_l}')">+ Añadir a esta lista</button>
        </div>
        """

    if not items_listas:
        items_listas = "<p style='color: var(--text-dim); padding: 10px 0;'>Aún no tienes listas creadas. Puedes crear una abajo para guardar esta canción.</p>"

    ruta_html = os.path.join(os.path.dirname(__file__), "agregar_a_lista.html")
    with open(ruta_html, "r", encoding="utf-8") as archivo:
        contenido = archivo.read()

    contenido = contenido.replace("<!-- BLOQUE_CANCION -->", bloque_cancion)
    contenido = contenido.replace("<!-- ITEMS_LISTAS -->", items_listas)
    return contenido

@app.get("/login", response_class=HTMLResponse)
def ruta_login():
    ruta_html = os.path.join(os.path.dirname(__file__), "login.html")
    with open(ruta_html, "r", encoding="utf-8") as archivo:
        return archivo.read()

@app.get("/registro", response_class=HTMLResponse)
def ruta_registro():
    ruta_html = os.path.join(os.path.dirname(__file__), "registro.html")
    with open(ruta_html, "r", encoding="utf-8") as archivo:
        return archivo.read()

# endpoints api
@app.post("/api/login")
async def api_login(request: Request):
    datos = await request.json()
    correo = datos.get("correo")
    contraseña = datos.get("contraseña")
    usuario_encontrado = iniciar_sesion(correo, contraseña)
    if usuario_encontrado is not None:
        return {"status": "ok", "usuario": usuario_encontrado}
    return JSONResponse(status_code=401, content={"status": "error", "mensaje": "Correo o contraseña incorrectos"})

@app.post("/api/registro")
async def api_registro(request: Request):
    datos = await request.json()
    nombre = datos.get("nombre")
    correo = datos.get("correo")
    contraseña = datos.get("contraseña")
    nuevo_id = registrar_usuario(nombre, correo, contraseña)
    if nuevo_id is not None:
        return {"status": "ok", "id": nuevo_id}
    return JSONResponse(status_code=400, content={"status": "error", "mensaje": "No se pudo registrar el usuario"})

@app.get("/api/catalogo")
def api_catalogo():
    canciones = ver_catalogo()
    if canciones is not None:
        return canciones
    return JSONResponse(status_code=500, content={"error": "Error al consultar catalogo"})

@app.get("/api/populares")
def api_populares():
    populares = ver_populares(10)
    if populares is not None:
        return populares
    return JSONResponse(status_code=500, content={"error": "Error al consultar populares"})

@app.get("/api/me-gusta")
def api_ver_me_gusta(id_usuario: int = 1):
    canciones = ver_canciones_me_gusta(id_usuario)
    if canciones is not None:
        return canciones
    return JSONResponse(status_code=500, content={"error": "Error al consultar canciones favoritas"})

@app.post("/api/me-gusta")
async def api_me_gusta(request: Request):
    datos = await request.json()
    id_usuario = int(datos.get("id_usuario", 1))
    id_cancion = int(datos.get("id_cancion"))
    le_gusta = alternar_me_gusta(id_usuario, id_cancion)
    if le_gusta is not None:
        return {"status": "ok", "le_gusta": le_gusta}
    return JSONResponse(status_code=500, content={"status": "error", "mensaje": "Error al actualizar Me gusta"})

@app.post("/api/subir")
async def api_subir(request: Request):
    # procesar y subir cancion
    datos = await request.json()
    enlace = datos.get("enlace", "").strip()
    id_usuario = int(datos.get("id_usuario", 1))

    if not enlace:
        return JSONResponse(status_code=400, content={"status": "error", "mensaje": "Debe ingresar un enlace de YouTube"})

    descarga = await asyncio.to_thread(descargar_musica_youtube, enlace)
    if not descarga:
        return JSONResponse(status_code=500, content={"status": "error", "mensaje": "No se pudo descargar la cancion de YouTube"})

    titulo = descarga["titulo"]
    artista = descarga["artista"]
    duracion = descarga["duracion"]
    id_youtube = descarga["id_youtube"]
    ruta_mp3 = descarga["ruta_archivo"]
    carpeta_temp = descarga["carpeta_temp"]

    nombre_en_r2 = f"audio/{id_youtube}.mp3"
    link_r2 = await asyncio.to_thread(subir_a_r2, ruta_mp3, nombre_en_r2)

    try:
        shutil.rmtree(carpeta_temp, ignore_errors=True)
    except Exception:
        pass

    if not link_r2:
        return JSONResponse(status_code=500, content={"status": "error", "mensaje": "Error al almacenar el audio en Cloudflare R2"})

    exito = ejecutar_sp_subir_cancion(titulo, id_youtube, artista, id_usuario, duracion, link_r2)
    if exito is not None:
        return {
            "status": "ok",
            "titulo": titulo,
            "artista": artista,
            "id_youtube": id_youtube,
            "duracion": duracion,
            "link_r2": link_r2
        }
    return JSONResponse(status_code=500, content={"status": "error", "mensaje": "Error al ejecutar sp_subir_cancion en MySQL"})

@app.get("/api/listas")
def api_listas(id_usuario: int = 1):
    listas = ver_listas_usuario(id_usuario)
    if listas is not None:
        return listas
    return JSONResponse(status_code=500, content={"error": "Error al consultar listas"})

@app.get("/api/listas/{id_lista}/canciones")
def api_canciones_lista(id_lista: int):
    canciones = ver_canciones_lista(id_lista)
    if canciones is not None:
        return canciones
    return JSONResponse(status_code=500, content={"error": "Error al consultar canciones de la lista"})

@app.post("/api/listas")
async def api_crear_lista(request: Request):
    datos = await request.json()
    id_usuario = int(datos.get("id_usuario", 0))
    nombre = datos.get("nombre", "").strip()
    if not nombre or not id_usuario:
        return JSONResponse(status_code=400, content={"status": "error", "mensaje": "Datos incompletos"})
    nuevo_id = crear_lista(id_usuario, nombre)
    if nuevo_id is not None:
        return {"status": "ok", "id": nuevo_id}
    return JSONResponse(status_code=500, content={"status": "error", "mensaje": "Error al crear la lista"})

@app.post("/api/listas/{id_lista}/agregar")
async def api_agregar_cancion_lista(id_lista: int, request: Request):
    datos = await request.json()
    id_cancion = datos.get("id_cancion")
    if not id_cancion:
        return JSONResponse(status_code=400, content={"status": "error", "mensaje": "Falta id_cancion"})
    exito = agregar_cancion_a_lista(id_lista, id_cancion)
    if exito:
        return {"status": "ok", "mensaje": "Canción agregada a la lista"}
    return JSONResponse(status_code=500, content={"status": "error", "mensaje": "No se pudo agregar la canción"})

@app.post("/api/listas/{id_lista}/eliminar")
async def api_eliminar_cancion_lista(id_lista: str, request: Request):
    datos = await request.json()
    id_cancion = datos.get("id_cancion")
    if not id_cancion:
        return JSONResponse(status_code=400, content={"status": "error", "mensaje": "Falta id_cancion"})
    
    if str(id_lista).lower() == "megusta" or str(id_lista) == "0":
        id_usuario = datos.get("id_usuario", 1)
        conexion = conectar()
        if conexion:
            cursor = conexion.cursor()
            cursor.execute("DELETE FROM me_gusta WHERE id_usuario = %s AND id_cancion = %s", (id_usuario, id_cancion))
            cursor.close()
            conexion.close()
            return {"status": "ok", "mensaje": "Canción quitada de Tus Me gusta"}
        return JSONResponse(status_code=500, content={"status": "error"})
    else:
        try:
            id_l = int(id_lista)
            exito = eliminar_cancion_de_lista(id_l, id_cancion)
            if exito:
                return {"status": "ok", "mensaje": "Canción eliminada de la lista"}
            return JSONResponse(status_code=500, content={"status": "error"})
        except Exception as e:
            return JSONResponse(status_code=400, content={"status": "error", "mensaje": str(e)})

@app.post("/api/listas/{id_lista}/eliminar-lista")
@app.delete("/api/listas/{id_lista}")
async def api_eliminar_lista(id_lista: str, request: Request):
    if str(id_lista).lower() in ("megusta", "0"):
        return JSONResponse(status_code=400, content={"status": "error", "mensaje": "La lista 'Canciones que te gustan' es automática del sistema y no se puede eliminar."})

    id_usuario = resolver_id_usuario(request)
    try:
        datos = await request.json()
        if datos and "id_usuario" in datos:
            id_usuario = int(datos["id_usuario"])
    except Exception:
        pass

    try:
        id_int = int(id_lista)
    except ValueError:
        return JSONResponse(status_code=400, content={"status": "error", "mensaje": "ID de lista inválido"})

    exito = eliminar_lista(id_int, id_usuario)
    if exito:
        return {"status": "ok", "mensaje": "Lista de reproducción eliminada con éxito"}
    return JSONResponse(status_code=500, content={"status": "error", "mensaje": "No se pudo eliminar la lista de la base de datos"})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
