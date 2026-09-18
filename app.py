import os

from flask import Flask, jsonify, request

app = Flask(__name__)

RESPUESTA = {"testCodePatch": True, "resetGuest": True}
METODOS = ["GET", "POST", "OPTIONS"]


@app.before_request
def registrar_peticion():
    print("===== PETICIÓN ENTRANTE =====", flush=True)
    print(f"IP: {request.remote_addr}", flush=True)
    print(f"Método: {request.method}", flush=True)
    print(f"Ruta: {request.full_path}", flush=True)
    print(f"URL completa: {request.url}", flush=True)
    print(f"Headers: {dict(request.headers)}", flush=True)
    print(f"Content-Type: {request.content_type}", flush=True)
    print(f"Content-Length: {request.content_length}", flush=True)
    print("=============================", flush=True)


@app.after_request
def agregar_cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response


@app.route("/", defaults={"path": ""}, methods=METODOS)
@app.route("/<path:path>", methods=METODOS)
def responder(path):
    # El body se ignora deliberadamente: GET, POST y OPTIONS reciben la misma respuesta.
    return jsonify(RESPUESTA), 200


if __name__ == "__main__":
    # En local usa 7777; Render proporciona PORT automáticamente.
    puerto = int(os.environ.get("PORT", 7777))
    app.run(host="0.0.0.0", port=puerto)
