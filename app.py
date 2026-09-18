import html
import json
import os
import threading
from datetime import datetime, timezone

from flask import Flask, Response, request

app = Flask(__name__)

LOG_FILE = os.environ.get("LOG_FILE", "peticiones.log")
LOG_LOCK = threading.Lock()
MAX_BODY_LOG_BYTES = 65536

JSON_BASE = {"testCodePatch": True, "resetGuest": True}
FORMATOS = {
    "formato1": JSON_BASE,
    "formato2": {"testCodePatch": "true", "resetGuest": "true"},
    "formato3": {"data": JSON_BASE},
    "formato4": {"status": "ok", "testCodePatch": True, "resetGuest": True},
    "formato5": {"success": True, "testCodePatch": True, "resetGuest": True},
}

VER_FORMATOS = ["json1", "json2", "json3", "json4", "json5", "json6", "json7", "json8", "json9", "json10", "text", "empty", "204"]
ACTIVE_VER_FMT = "json1"
FMT_LOCK = threading.Lock()

# Rotación automática usada exclusivamente por /ver.php.
ROTACION_FORMATOS = [
    "json1", "json2", "json3", "json4", "json5", "json6", "json7", "json8", "json9", "json10",
    "json11", "json12", "json13", "json14", "json15", "json16", "json17", "text", "empty", "204",
]
CONTADOR_VER = 0
COUNTER_LOCK = threading.Lock()


def ahora():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def serializar_body(body_bytes):
    if not body_bytes:
        return {"bytes": 0, "text": "", "encoding": "empty"}

    limitado = body_bytes[:MAX_BODY_LOG_BYTES]
    try:
        texto = limitado.decode("utf-8")
        encoding = "utf-8"
    except UnicodeDecodeError:
        texto = limitado.decode("utf-8", errors="replace")
        encoding = "utf-8-with-replacements"

    return {
        "bytes": len(body_bytes),
        "truncated": len(body_bytes) > MAX_BODY_LOG_BYTES,
        "encoding": encoding,
        "text": texto,
        "hex_preview": limitado[:256].hex(),
    }


def guardar_peticion(registro):
    linea = json.dumps(registro, ensure_ascii=False, separators=(",", ":"))
    with LOG_LOCK:
        with open(LOG_FILE, "a", encoding="utf-8") as archivo:
            archivo.write(linea + "\n")
            archivo.flush()
    print(linea, flush=True)


def respuesta_texto(body, content_type="application/json; charset=utf-8", status=200):
    cuerpo = body.encode("utf-8")
    respuesta = Response(cuerpo, status=status)
    respuesta.headers["Content-Type"] = content_type
    respuesta.headers["Content-Length"] = str(len(cuerpo))
    respuesta.headers["Connection"] = "close"
    respuesta.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    respuesta.headers["Pragma"] = "no-cache"
    respuesta.headers["Expires"] = "0"
    return respuesta


def codigo_respuesta_solicitado(default=200):
    valor = request.args.get("status", str(default))
    try:
        codigo = int(valor)
    except ValueError:
        return default
    return codigo if codigo in (200, 201) else default


@app.before_request
def registrar_peticion():
    body = request.get_data(cache=True, as_text=False)
    registro = {
        "timestamp": ahora(),
        "ip": request.remote_addr,
        "method": request.method,
        "path": request.path,
        "full_path": request.full_path,
        "url": request.url,
        "query_params": request.args.to_dict(flat=False),
        "user_agent": request.headers.get("User-Agent", ""),
        "content_type": request.content_type,
        "content_length_header": request.headers.get("Content-Length"),
        "headers": dict(request.headers),
        "body": serializar_body(body),
    }
    request.environ["diagnostic_record"] = registro
    guardar_peticion(registro)
    print("===== PETICIÓN DETALLADA RECIBIDA =====", flush=True)
    print(f"Timestamp: {registro['timestamp']}", flush=True)
    print(f"IP: {registro['ip']}", flush=True)
    print(f"Método: {registro['method']}", flush=True)
    print(f"Ruta: {registro['full_path']}", flush=True)
    print(f"User-Agent: {registro['user_agent']}", flush=True)
    print(f"Headers: {registro['headers']}", flush=True)
    print(f"Body: {registro['body']}", flush=True)
    print("========================================", flush=True)


@app.after_request
def registrar_respuesta(respuesta):
    respuesta.headers["Access-Control-Allow-Origin"] = "*"
    respuesta.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS, HEAD"
    respuesta.headers["Access-Control-Allow-Headers"] = "*"

    registro = request.environ.get("diagnostic_record", {})
    salida = {
        "timestamp": ahora(),
        "type": "response",
        "request_timestamp": registro.get("timestamp"),
        "method": request.method,
        "path": request.full_path,
        "status_code": respuesta.status_code,
        "verver_request_number": request.environ.get("verver_request_number"),
        "verver_format_requested": request.environ.get("verver_format_requested"),
        "verver_query_params": request.environ.get("verver_query_params"),
        "headers": dict(respuesta.headers),
        "body": respuesta.get_data(as_text=True),
    }
    print("===== RESPUESTA DETALLADA ENVIADA =====", flush=True)
    texto_salida = json.dumps(salida, ensure_ascii=False, indent=2)
    print(texto_salida, flush=True)
    print("========================================", flush=True)

    # Persistir también la respuesta de /ver.php para poder correlacionarla en /debug.
    if request.path == "/ver.php":
        guardar_peticion(salida)
    return respuesta


@app.route("/debug", methods=["GET", "POST", "OPTIONS"])
def debug():
    registros = []
    if os.path.exists(LOG_FILE):
        with LOG_LOCK:
            with open(LOG_FILE, "r", encoding="utf-8") as archivo:
                for linea in archivo.readlines()[-200:]:
                    try:
                        registros.append(json.loads(linea))
                    except json.JSONDecodeError:
                        registros.append({"raw": linea.rstrip()})
    registros.reverse()
    bloques = []
    for registro in registros:
        bloques.append(f"<pre>{html.escape(json.dumps(registro, ensure_ascii=False, indent=2))}</pre>")
    contenido = "\n".join(bloques) or "<p>No se ha registrado ninguna petición todavía.</p>"
    pagina = f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><title>Panel de diagnóstico</title>
<style>body{{font-family:monospace;background:#111;color:#eee;padding:20px}}pre{{white-space:pre-wrap;background:#222;border:1px solid #555;padding:12px;margin:12px 0}}h1{{font-family:sans-serif}}</style>
</head><body><h1>Panel de diagnóstico</h1><p>Archivo: {html.escape(LOG_FILE)}. Últimas 200 entradas, más recientes primero.</p>{contenido}</body></html>"""
    return respuesta_texto(pagina, "text/html; charset=utf-8", 200)


@app.route("/formato1", methods=["GET", "POST", "OPTIONS"])
@app.route("/formato2", methods=["GET", "POST", "OPTIONS"])
@app.route("/formato3", methods=["GET", "POST", "OPTIONS"])
@app.route("/formato4", methods=["GET", "POST", "OPTIONS"])
@app.route("/formato5", methods=["GET", "POST", "OPTIONS"])
def formato_prueba():
    nombre = request.path.strip("/")
    body = json.dumps(FORMATOS[nombre], ensure_ascii=False, separators=(", ", ": "))
    return respuesta_texto(body, "application/json; charset=utf-8", codigo_respuesta_solicitado(200))


@app.route("/codigo/<int:codigo>", methods=["GET", "POST", "OPTIONS"])
def codigo_prueba(codigo):
    status = codigo if codigo in (200, 201) else 200
    body = json.dumps(JSON_BASE, ensure_ascii=False, separators=(", ", ": "))
    return respuesta_texto(body, "application/json; charset=utf-8", status)


def formato_actual():
    with FMT_LOCK:
        return ACTIVE_VER_FMT


def establecer_formato(nombre):
    global ACTIVE_VER_FMT
    with FMT_LOCK:
        ACTIVE_VER_FMT = nombre
        return ACTIVE_VER_FMT


@app.route("/set_fmt/<nombre>", methods=["GET", "POST", "OPTIONS"])
def set_fmt(nombre):
    nombre = nombre.lower()
    if nombre not in VER_FORMATOS:
        return respuesta_texto("formato no válido: " + nombre, "text/plain; charset=utf-8", 400)
    establecer_formato(nombre)
    return respuesta_texto("ok", "text/plain; charset=utf-8", 200)


@app.route("/get_fmt", methods=["GET", "POST", "OPTIONS"])
def get_fmt():
    return respuesta_texto(formato_actual(), "text/plain; charset=utf-8", 200)


@app.route("/rotar", methods=["GET", "POST", "OPTIONS"])
def rotar():
    actual = formato_actual()
    siguiente = VER_FORMATOS[(VER_FORMATOS.index(actual) + 1) % len(VER_FORMATOS)]
    establecer_formato(siguiente)
    return respuesta_texto(siguiente, "text/plain; charset=utf-8", 200)


def json_body(payload):
    return respuesta_texto(json.dumps(payload, ensure_ascii=False, separators=(", ", ": ")), "application/json; charset=utf-8", 200)


@app.route("/reset_contador", methods=["GET", "POST", "OPTIONS"])
def reset_contador():
    global CONTADOR_VER
    with COUNTER_LOCK:
        CONTADOR_VER = 0
    return respuesta_texto("contador: 0\npróximo formato: json1\n", "text/plain; charset=utf-8", 200)


@app.route("/estado", methods=["GET", "POST", "OPTIONS"])
def estado():
    with COUNTER_LOCK:
        contador = CONTADOR_VER
        siguiente = ROTACION_FORMATOS[contador % len(ROTACION_FORMATOS)]
    texto = (
        f"contador actual: {contador}\n"
        f"próximo formato: {siguiente}\n"
        f"total formatos: {len(ROTACION_FORMATOS)}\n"
        f"formatos: {', '.join(ROTACION_FORMATOS)}\n"
    )
    return respuesta_texto(texto, "text/plain; charset=utf-8", 200)


@app.route("/ver.php", methods=["GET", "POST", "OPTIONS", "HEAD"])
def ver_php():
    """Endpoint Unity: cada llamada incrementa el contador y consume el siguiente formato."""
    global CONTADOR_VER
    parametros = request.args.to_dict(flat=False)
    with COUNTER_LOCK:
        CONTADOR_VER += 1
        numero = CONTADOR_VER
        fmt = ROTACION_FORMATOS[(numero - 1) % len(ROTACION_FORMATOS)]

    version = request.args.get("version", "1.132.6")
    release_version = request.args.get("release_version", "OB55")
    whitelist_version = request.args.get("whitelist_version", "1.8.0")
    whitelist_sp_version = request.args.get("whitelist_sp_version", "1.0.0")
    request.environ["verver_request_number"] = numero
    request.environ["verver_format_requested"] = fmt
    request.environ["verver_query_params"] = parametros

    if fmt == "json1":
        return json_body({"version": version, "status": "ok", "force_update": False, "url": ""})
    if fmt == "json2":
        return json_body({"latest_version": version, "release_version": release_version, "status": "ok"})
    if fmt == "json3":
        return json_body({"code": 0, "msg": "ok", "data": {"version": version, "whitelist_version": whitelist_version, "whitelist_sp_version": whitelist_sp_version}})
    if fmt == "json4":
        return json_body({"code": 200, "message": "success", "version": version, "whitelist": {"version": whitelist_version, "sp_version": whitelist_sp_version}})
    if fmt == "json5":
        return json_body({"status": 1, "version": version, "force": 0, "url": "", "whitelist": 1})
    if fmt == "json6":
        return json_body({"result": "ok", "version": version, "update": False})
    if fmt == "json7":
        return json_body({"version": version, "url": "", "md5": "", "size": 0, "force": False})
    if fmt == "json8":
        return json_body({"ret": 0, "version": version, "data": "", "msg": ""})
    if fmt == "json9":
        return json_body({"code": 0, "version": version, "whitelist_version": whitelist_version, "whitelist_sp_version": whitelist_sp_version, "force_update": False, "update_url": ""})
    if fmt == "json10":
        return json_body({"status": "success", "data": {"version": version, "release_version": release_version}})
    if fmt == "json11":
        return json_body({"whitelist_version": whitelist_version, "whitelist_sp_version": whitelist_sp_version, "status": "ok"})
    if fmt == "json12":
        return json_body({"version": version, "whitelist_version": whitelist_version, "whitelist_sp_version": whitelist_sp_version, "status": "ok", "force_update": False, "url": ""})
    if fmt == "json13":
        return json_body({"code": 0, "whitelist": {"version": whitelist_version, "sp_version": whitelist_sp_version}, "version": version, "url": ""})
    if fmt == "json14":
        return json_body({"success": True, "whitelist_version": whitelist_version, "whitelist_sp_version": whitelist_sp_version, "version": version, "force_update": False, "url": "", "token": ""})
    if fmt == "json15":
        return json_body({"status": "success", "data": {"whitelist_version": whitelist_version, "whitelist_sp_version": whitelist_sp_version, "version": version, "force_update": False, "url": "", "token": ""}})
    if fmt == "json16":
        return json_body({"ret": 0, "data": {"whitelist_version": whitelist_version, "whitelist_sp_version": whitelist_sp_version, "version": version}, "msg": "ok"})
    if fmt == "json17":
        return json_body({"status": 0, "msg": "", "data": {"version": version, "whitelist_version": whitelist_version, "whitelist_sp_version": whitelist_sp_version}})
    if fmt == "text":
        return respuesta_texto("", "text/plain; charset=utf-8", 200)
    if fmt == "empty":
        return respuesta_texto("", "application/octet-stream", 200)
    return respuesta_texto("", "application/octet-stream", 204)


@app.route("/verver.php", methods=["GET", "POST", "OPTIONS", "HEAD"])
def verver_php():
    """Compatibilidad con clientes antiguos que concatena verver.php."""
    return ver_php()


@app.route("/verver.php/empty", methods=["GET", "POST", "OPTIONS", "HEAD"])
def verver_empty():
    request.environ["verver_format_requested"] = "path-empty"
    return respuesta_texto("", "application/octet-stream", 200)


@app.route("/plain", methods=["GET", "POST", "OPTIONS"])
def plain():
    return respuesta_texto('{"testCodePatch": true, "resetGuest": true}', "text/plain; charset=utf-8", codigo_respuesta_solicitado(200))


@app.route("/health", methods=["GET", "POST", "OPTIONS"])
def health():
    return respuesta_texto("ok", "text/plain; charset=utf-8", 200)


@app.route("/", defaults={"path": ""}, methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
@app.route("/<path:path>", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
def catch_all(path):
    body = json.dumps(JSON_BASE, ensure_ascii=False, separators=(", ", ": "))
    return respuesta_texto(body, "application/json; charset=utf-8", codigo_respuesta_solicitado(200))


if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 7777))
    app.run(host="0.0.0.0", port=puerto, threaded=True)
