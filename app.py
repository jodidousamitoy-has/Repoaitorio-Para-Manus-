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
        "headers": dict(respuesta.headers),
        "body": respuesta.get_data(as_text=True),
    }
    print("===== RESPUESTA DETALLADA ENVIADA =====", flush=True)
    print(json.dumps(salida, ensure_ascii=False, indent=2), flush=True)
    print("========================================", flush=True)
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
