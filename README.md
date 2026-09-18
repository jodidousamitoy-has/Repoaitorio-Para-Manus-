# Servidor JSON Flask

Servidor HTTP mínimo escrito en Python con Flask. Responde siempre con el siguiente JSON:

```json
{"testCodePatch": true, "resetGuest": true}
```

El servidor no utiliza autenticación, base de datos ni lógica adicional. Acepta peticiones `GET` y `POST` en `/`, `/config` y `/ver`, devuelve `Content-Type: application/json` e imprime en consola la IP de origen de cada petición.

## Archivos

| Archivo | Función |
|---|---|
| `app.py` | Servidor Flask y definición de las rutas. |
| `requirements.txt` | Dependencia de Flask. |
| `Procfile` | Comando de inicio para plataformas compatibles, incluido Render. |
| `README.md` | Instrucciones de ejecución, prueba y despliegue. |

## Ejecución local

Necesitas Python 3 instalado. Desde la carpeta del proyecto, crea y activa un entorno virtual:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

En Windows PowerShell, activa el entorno con:

```powershell
.venv\Scripts\Activate.ps1
```

Instala Flask y arranca el servidor:

```bash
pip install -r requirements.txt
python app.py
```

El proceso quedará escuchando en `0.0.0.0:7777`. En el mismo equipo, la URL de prueba es:

```text
http://localhost:7777/
```

Para detenerlo, pulsa `Ctrl+C` en la terminal.

## Pruebas con curl

Prueba la ruta raíz con `GET`:

```bash
curl http://localhost:7777/
```

La respuesta esperada es:

```json
{"resetGuest":true,"testCodePatch":true}
```

El orden de las claves puede variar porque Flask serializa el objeto JSON; los nombres y valores son exactamente los solicitados.

Prueba también `POST` y las demás rutas:

```bash
curl -X POST http://localhost:7777/
curl http://localhost:7777/config
curl -X POST http://localhost:7777/config
curl http://localhost:7777/ver
curl -X POST http://localhost:7777/ver
```

Cada petición aparecerá en la consola del servidor con un mensaje similar a:

```text
Petición desde: 127.0.0.1
```

## Despliegue gratuito en Render

Render permite desplegar un servicio web conectando un repositorio Git y configurando un comando de compilación y otro de inicio. La guía oficial de Flask para Render indica utilizar un servicio **Web Service**, instalar las dependencias con `pip install -r requirements.txt` y arrancar la aplicación con un comando de servidor Python [1]. La documentación general de Render también indica que los servicios web deben escuchar en `0.0.0.0` para recibir tráfico público [2].

### 1. Subir el proyecto a GitHub

Crea un repositorio nuevo en GitHub y sube estos cuatro archivos en la raíz del repositorio:

```text
app.py
requirements.txt
Procfile
README.md
```

Desde una terminal, si todavía no has creado el repositorio local, puedes ejecutar:

```bash
git init
git add app.py requirements.txt Procfile README.md
git commit -m "Crear servidor JSON Flask"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/TU_REPOSITORIO.git
git push -u origin main
```

Sustituye `TU_USUARIO/TU_REPOSITORIO` por los datos reales de tu repositorio.

### 2. Crear el servicio en Render

1. Entra en [Render Dashboard](https://dashboard.render.com/) e inicia sesión.
2. Selecciona **New** y después **Web Service**.
3. Conecta GitHub y selecciona el repositorio que contiene estos archivos.
4. Configura el servicio con estos valores:

| Campo de Render | Valor |
|---|---|
| **Name** | Un nombre único, por ejemplo `servidor-json-juego`. |
| **Language** | `Python 3`. |
| **Branch** | `main`. |
| **Build Command** | `pip install -r requirements.txt`. |
| **Start Command** | `python app.py`. |
| **Instance Type / Plan** | `Free`, si aparece disponible en tu cuenta. |

5. Pulsa **Create Web Service**.
6. Espera a que termine el build y el deploy. Render mostrará una URL pública con formato parecido a:

```text
https://servidor-json-juego.onrender.com
```

La URL exacta la asigna Render; no copies literalmente el ejemplo. En el primer despliegue, revisa los logs del servicio y confirma que aparece el mensaje de Flask indicando que escucha en el puerto `7777`.

### 3. Probar la URL pública

Cuando Render haya terminado, sustituye la URL de ejemplo por la URL real:

```bash
curl https://servidor-json-juego.onrender.com/
curl https://servidor-json-juego.onrender.com/config
curl -X POST https://servidor-json-juego.onrender.com/ver
```

Las tres peticiones deben devolver el mismo objeto JSON. Para el cliente del juego, normalmente debes usar la URL base sin añadir una ruta, si el cliente apunta a `/`:

```text
https://servidor-json-juego.onrender.com/
```

Si tu cliente solicita específicamente `/config` o `/ver`, utiliza la ruta correspondiente:

```text
https://servidor-json-juego.onrender.com/config
https://servidor-json-juego.onrender.com/ver
```

### Nota sobre el plan gratuito

Los planes gratuitos de plataformas de alojamiento pueden suspender o ralentizar temporalmente un servicio cuando no recibe tráfico. Si una primera petición tarda más de lo habitual, espera unos segundos y vuelve a intentarlo. El servicio no guarda datos y no necesita variables de entorno.

## Ejemplo de `localconfig.json`

Si el cliente espera una URL base, el archivo puede quedar así:

```json
{
  "serverUrl": "https://servidor-json-juego.onrender.com/"
}
```

Si tu cliente utiliza otro nombre de propiedad, conserva el nombre que exige tu juego y coloca la URL pública de Render como valor. Por ejemplo, si espera `configUrl`:

```json
{
  "configUrl": "https://servidor-json-juego.onrender.com/config"
}
```

No incluyes las dos propiedades a menos que tu cliente las utilice. La URL debe ser la URL real asignada por Render, preferiblemente con `https://`.

## Referencias

[1]: https://render.com/docs/deploy-flask "Render: Deploy a Flask App on Render"

[2]: https://render.com/docs/web-services "Render: Web Services"
