import os

from flask import Flask, Response, request

app = Flask(__name__)

JSON_BODY = '{"testCodePatch": true, "resetGuest": true}'
PLAIN_BODY = JSON_BODY
HEALTH_BODY = "ok"
METODOS = ["GET", "POST", "OPTIONS"]


def crear_respuesta(body, content_type):
    cuerpo = body.encode("utf-8")
    respuesta = Response(cuerpo, status=200)
    respuesta.headers["Content-Type"] = content_type
    respuesta.headers["Content-Length"] = str(len(cuerpo))
    respuesta.headers["Connection"] = "close"
    respuesta.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    respuesta.headers["Pragma"] = "no-cache"
    respuesta.headers["Expires"] = "0"
    return respuesta


@app.before_request
def registrar_peticion():
    print("===== PETICIÓN ENTRANTE =====", flush=True)
    print(f"IP: {request.remote_addr}", flush=True)
    print(f"Método: {request.method}", flush=True)
    print(f"Ruta: {request.full_path}", flush=True)
    print(f"URL completa: {request.url}", flush=True)
    print(f"Headers recibidos: {dict(request.headers)}", flush=True)
    print(f"Content-Type recibido: {request.content_type}", flush=True)
    print(f"Content-Length recibido: {request.content_length}", flush=True)
    print("=============================", flush=True)


@app.after_request
def agregar_cors_y_registrar_respuesta(respuesta):
    respuesta.headers["Access-Control-Allow-Origin"] = "*"
    respuesta.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    respuesta.headers["Access-Control-Allow-Headers"] = "*"

    print("===== RESPUESTA ENVIADA =====", flush=True)
    print(f"Status code: {respuesta.status_code}", flush=True)
    print(f"Headers enviados: {dict(respuesta.headers)}", flush=True)
    print(f"Body enviado: {respuesta.get_data(as_text=True)}", flush=True)
    print("=============================", flush=True)
    return respuesta


@app.route("/plain", methods=METODOS)
def plain():
    return crear_respuesta(PLAIN_BODY, "text/plain; charset=utf-8")


@app.route("/health", methods=METODOS)
def health():
    return crear_respuesta(HEALTH_BODY, "text/plain; charset=utf-8")


@app.route("/", defaults={"path": ""}, methods=METODOS)
@app.route("/<path:path>", methods=METODOS)
def catch_all(path):
    # Se ignoran deliberadamente el body, el Content-Type y los headers del cliente.
    return crear_respuesta(JSON_BODY, "application/json; charset=utf-8")


if __name__ == "__main__":
    # En local usa 7777; Render proporciona PORT automáticamente.
    puerto = int(os.environ.get("PORT", 7777))
    app.run(host="0.0.0.0", port=puerto, threaded=True)
