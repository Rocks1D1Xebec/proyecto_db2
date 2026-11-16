import os # Maneja rutas de archivos en el sistema operativo (para encontrar y abrir los archivos HTML)
import pymysql # Conector oficial de Python para comunicarse y hacer consultas con MySQL
from pymysql.cursors import DictCursor # Hace que las filas de MySQL se lean como diccionarios {'columna': 'valor'}
from fastapi import FastAPI, Request # Crear el servidor web y definir las rutas (/login, /catalogo, etc.), permite recibir y leer los datos que el usuario envia desde el formulario HTML
from fastapi.responses import HTMLResponse, JSONResponse # Indica al navegador que le estamos enviando una pagina visual en HTML, envia respuestas de datos estructurados en formato JSON al navegador
import uvicorn # Servidor web ligero que mantiene corriendo y escuchando la aplicacion en el puerto 8000

servidor = "localhost"
usuario = "nyls"
clave = "nyls123"
base_datos = "lyra"
puerto = 3307

app = FastAPI()

def conectar():
    try:
        conexion = pymysql.connect(
            host=servidor,
            user=usuario,
            password=clave,
            database=base_datos,
            port=puerto,
            charset="utf8mb4",
            cursorclass=DictCursor,
            connect_timeout=2,
            autocommit=True
        )
        return conexion
    except Exception as error:
        # Si falla por IP publica (por ejemplo, dentro de la misma maquina virtual de Oracle), intenta por localhost
        try:
            conexion = pymysql.connect(
                host="localhost",
                user=usuario,
                password=clave,
                database=base_datos,
                port=3306,
                charset="utf8mb4",
                cursorclass=DictCursor,
                connect_timeout=2,
                autocommit=True
            )
            return conexion
        except Exception:
            print("Error de conexion:", error)
            return None

def iniciar_sesion(correo, contraseña):
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
    conexion = conectar()
    if not conexion:
        return None
    try:
        cursor = conexion.cursor()
        cursor.callproc("sp_subir_cancion", (titulo, id_youtube, artista, id_usuario, duracion, link_r2))
        cursor.close()
        conexion.close()
        return True
    except Exception as error:
        print("Error en ejecutar_sp_subir_cancion:", error)
        return None

def dar_me_gusta(id_usuario, id_cancion):
    conexion = conectar()
    if not conexion:
        return None
    try:
        cursor = conexion.cursor()
        sql = "INSERT INTO me_gusta (id_usuario, id_cancion) VALUES (%s, %s) ON DUPLICATE KEY UPDATE fecha_agregado = CURRENT_TIMESTAMP"
        cursor.execute(sql, (id_usuario, id_cancion))
        cursor.close()
        conexion.close()
        return True
    except Exception as error:
        print("Error en dar_me_gusta:", error)
        return None

def ver_listas_usuario(id_usuario):
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

def ver_canciones_lista(id_lista):
    conexion = conectar()
    if not conexion:
        return None
    try:
        cursor = conexion.cursor()
        sql = """
            SELECT c.id AS id_cancion, c.titulo, a.nombre AS artista, c.duracion, d.posicion
            FROM detalle_lista d
            INNER JOIN cancion c ON d.id_cancion = c.id
            INNER JOIN artista a ON c.id_artista = a.id
            WHERE d.id_lista = %s
            ORDER BY d.posicion ASC
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
    conexion = conectar()
    if not conexion:
        return None
    try:
        cursor = conexion.cursor()
        sql = "INSERT INTO lista (nombre, id_usuario) VALUES (%s, %s)"
        cursor.execute(sql, (nombre, id_usuario))
        nuevo_id = cursor.lastrowid
        cursor.close()
        conexion.close()
        return nuevo_id
    except Exception as error:
        print("Error en crear_lista:", error)
        return None

def agregar_cancion_a_lista(id_lista, id_cancion):
    conexion = conectar()
    if not conexion:
        return None
    try:
        cursor = conexion.cursor()
        cursor.execute("SELECT COALESCE(MAX(posicion), 0) + 1 AS siguiente FROM detalle_lista WHERE id_lista = %s", (id_lista,))
        posicion = cursor.fetchone()["siguiente"]
        sql = "INSERT INTO detalle_lista (id_lista, id_cancion, posicion) VALUES (%s, %s, %s)"
        cursor.execute(sql, (id_lista, id_cancion, posicion))
        cursor.close()
        conexion.close()
        return True
    except Exception as error:
        print("Error en agregar_cancion_a_lista:", error)
        return None

# conectar html y python

@app.get("/", response_class=HTMLResponse)
def ruta_inicio():
    ruta_html = os.path.join(os.path.dirname(__file__), "index.html")
    try:
        with open(ruta_html, "r", encoding="utf-8") as archivo:
            return archivo.read()
    except Exception as error:
        return f"<h1>Error al cargar index.html: {error}</h1>"

@app.get("/login", response_class=HTMLResponse)
def ruta_login():
    ruta_html = os.path.join(os.path.dirname(__file__), "login.html")
    try:
        with open(ruta_html, "r", encoding="utf-8") as archivo:
            return archivo.read()
    except Exception as error:
        return f"<h1>Error al cargar login.html: {error}</h1>"

@app.get("/registro", response_class=HTMLResponse)
def ruta_registro():
    ruta_html = os.path.join(os.path.dirname(__file__), "registro.html")
    try:
        with open(ruta_html, "r", encoding="utf-8") as archivo:
            return archivo.read()
    except Exception as error:
        return f"<h1>Error al cargar registro.html: {error}</h1>"

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

@app.post("/api/login")
async def api_login(request: Request):
    datos = await request.json()
    correo = datos.get("correo")
    contraseña = datos.get("contraseña")
    usuario_encontrado = iniciar_sesion(correo, contraseña)
    if usuario_encontrado is not None:
        return {"status": "ok", "usuario": usuario_encontrado}
    return JSONResponse(status_code=401, content={"status": "error", "mensaje": "Credenciales invalidas"})

@app.post("/api/registro")
async def api_registro(request: Request):
    datos = await request.json()
    nombre = datos.get("nombre")
    correo = datos.get("correo")
    contraseña = datos.get("contraseña")
    nuevo_id = registrar_usuario(nombre, correo, contraseña)
    if nuevo_id is not None:
        return {"status": "ok", "id": nuevo_id}
    return JSONResponse(status_code=400, content={"status": "error", "mensaje": "Error al registrar usuario"})

@app.post("/api/me-gusta")
async def api_me_gusta(request: Request):
    datos = await request.json()
    id_usuario = int(datos.get("id_usuario", 1))
    id_cancion = int(datos.get("id_cancion"))
    exito = dar_me_gusta(id_usuario, id_cancion)
    if exito is not None:
        return {"status": "ok"}
    return JSONResponse(status_code=500, content={"status": "error", "mensaje": "Error al registrar like"})

def extraer_id_youtube(enlace):
    # Extrae el identificador unico de YouTube del enlace
    if "v=" in enlace:
        return enlace.split("v=")[1].split("&")[0]
    elif "youtu.be/" in enlace:
        return enlace.split("youtu.be/")[1].split("?")[0]
    return enlace

@app.post("/api/subir")
async def api_subir(request: Request):
    datos = await request.json()
    enlace = datos.get("enlace", "")
    id_usuario = int(datos.get("id_usuario", 1))

    # Sacamos el ID de YouTube desde el enlace proporcionado
    id_youtube = extraer_id_youtube(enlace)

    # Datos temporales hasta implementar la libreria de YouTube y R2
    titulo = f"Cancion ({id_youtube})"
    artista = "Artista Desconocido"
    duracion = 180
    link_r2 = ""

    # Ejecuta el procedimiento almacenado sp_subir_cancion en MySQL
    exito = ejecutar_sp_subir_cancion(titulo, id_youtube, artista, id_usuario, duracion, link_r2)
    if exito is not None:
        return {"status": "ok"}
    return JSONResponse(status_code=500, content={"status": "error", "mensaje": "Error al registrar cancion"})

@app.get("/api/listas")
def api_listas(id_usuario: int):
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
    return JSONResponse(status_code=500, content={"status": "error", "mensaje": "Error al crear lista"})

@app.post("/api/listas/agregar")
async def api_agregar_a_lista(request: Request):
    datos = await request.json()
    id_lista = int(datos.get("id_lista", 0))
    id_cancion = int(datos.get("id_cancion", 0))
    if not id_lista or not id_cancion:
        return JSONResponse(status_code=400, content={"status": "error", "mensaje": "Datos incompletos"})
    exito = agregar_cancion_a_lista(id_lista, id_cancion)
    if exito is not None:
        return {"status": "ok"}
    return JSONResponse(status_code=500, content={"status": "error", "mensaje": "Error o cancion ya agregada"})

# Iniciar servidor web
if __name__ == "__main__":
    print("INICIANDO SERVIDOR WEB LYRA MUSIC")
    print("Pagina principal: http://localhost:8000")
    print("Iniciar sesion: http://localhost:8000/login")
    print("Registro: http://localhost:8000/registro")
    uvicorn.run(app, host="0.0.0.0", port=8000)
