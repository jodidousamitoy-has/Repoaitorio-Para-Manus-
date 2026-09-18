from flask import Flask, jsonify, request

app = Flask(__name__)

RESPUESTA = {"testCodePatch": True, "resetGuest": True}


@app.route("/", methods=["GET", "POST"])
@app.route("/config", methods=["GET", "POST"])
@app.route("/ver", methods=["GET", "POST"])
def raiz():
    print(f"Petición desde: {request.remote_addr}", flush=True)
    return jsonify(RESPUESTA)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7777)
