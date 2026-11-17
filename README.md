# MOIA – Agente clasificador de archivos

Agente conversacional que organiza archivos de texto por temas. Recibe archivos en una carpeta de **recepción**, lee su contenido, decide a qué tema pertenecen (tecnología, deportes, recetas, finanzas u otros) y los mueve a la carpeta correspondiente.

El agente está construido con **LangGraph** (agente ReAct) y accede al sistema de archivos a través de un servidor **MCP** (Model Context Protocol). El modelo de lenguaje es intercambiable entre **Google Gemini** (en la nube) y **Ollama** (local) cambiando solo el archivo `.env`.

## Cómo funciona

```
Usuario ──► agente_graph.py (LangGraph + LLM)
                 │  cliente MCP (stdio)
                 ▼
            mcp_server.py ──► descargas/ ──► recepcion/ ──► clasificados/<tema>/
```

1. `agente_graph.py` arranca el servidor MCP como subproceso y se conecta a él por stdio.
2. Las herramientas del servidor se exponen al agente como *tools* de LangChain.
3. El usuario chatea con el agente por consola. El agente solo actúa sobre los archivos mediante las herramientas del servidor MCP.
4. Para clasificar, el agente:
   1. lista los archivos de `recepcion/`,
   2. lee el contenido de cada uno,
   3. elige un tema de la lista prefijada basándose solo en el contenido,
   4. mueve el archivo a `clasificados/<tema>/` (la carpeta se crea si no existe).
5. Subir un archivo o guardar un texto **no** lo clasifica: la clasificación solo se hace cuando el usuario lo pide.
6. El agente conserva el historial de la sesión, así que entiende preguntas de seguimiento como «¿Y en finanzas?».

## Estructura del proyecto

```
MOIA_agente_clasificador/
├── agente_graph.py     # Agente LangGraph, selección de LLM y chat por consola
├── mcp_server.py       # Servidor MCP con las herramientas de archivos
├── requirements.txt    # Dependencias
├── .env                # Tu API key y modelo (no se sube a git)
├── .env.example        # Plantilla de variables de entorno
├── .gitignore
├── descargas/          # Origen simulado de archivos (se crea sola)
├── recepcion/          # Archivos pendientes de clasificar (se crea sola)
└── clasificados/       # Resultado: una subcarpeta por tema (se crea sola)
```

## Requisitos

- Python 3.10 o superior. Se ha probado con **Python 3.13**; con versiones muy recientes algunas dependencias pueden no tener paquetes precompilados y obligar a compilar (en Windows, requiere las Microsoft C++ Build Tools).
- Una API key de Google Gemini (si usas Gemini) **o** [Ollama](https://ollama.com) instalado con un modelo descargado que soporte *tool calling* (si usas el modo local).

## Instalación

Desde la carpeta del proyecto, con `venv` y `pip` (Windows, PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

En Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Alternativa con [uv](https://docs.astral.sh/uv/), que puede descargar la versión de Python que le pidas:

```powershell
uv venv --python 3.13
.venv\Scripts\Activate.ps1
uv pip install -r requirements.txt
```

## Configuración

Copia la plantilla y rellénala:

```powershell
copy .env.example .env
```

El archivo `.env` usa tres variables:

| Variable | Valores | Efecto |
|---|---|---|
| `GEMINI_API_KEY` | Tu clave de Google AI Studio | Solo es necesaria con el proveedor `gemini` |
| `LLM_PROVIDER` | `gemini` u `ollama` | Elige el proveedor. Si no se define, se usa `gemini` |
| `LLM_MODEL` | Nombre del modelo, p. ej. `gemini-3.5-flash-lite` o `llama3.1` | Elige el modelo concreto. Si no se define, se usa uno por defecto según el proveedor (`gemini-2.5-flash` o `llama3.1`) |

> No subas nunca el archivo `.env` a git ni lo compartas. Ya está incluido en `.gitignore`.

### Elegir el modelo

Para usar **Gemini**:

```
GEMINI_API_KEY=tu_api_key
LLM_PROVIDER=gemini
LLM_MODEL=gemini-3.5-flash-lite
```

Para usar **Ollama** en local (no necesita clave):

```
LLM_PROVIDER=ollama
LLM_MODEL=llama3.1
```

Después de editar el `.env`, reinicia el programa: el archivo solo se lee al arrancar.

Con Ollama, asegúrate de tener el servicio en marcha y el modelo descargado (`ollama pull llama3.1`). Los modelos pequeños pueden equivocarse al llamar a las herramientas.

Internamente, `main()` lee estas variables y se las pasa a la función `get_llm(provider, model_name)`, que devuelve el cliente de LangChain correspondiente (`ChatGoogleGenerativeAI` o `ChatOllama`) o lanza un error si el proveedor no es válido. El resto del programa no depende del proveedor elegido.

> Los nombres de los modelos de Gemini se retiran con el tiempo (por ejemplo, `gemini-2.5-flash-lite` ya devuelve un error 404 en cuentas nuevas). Define siempre `LLM_MODEL` en el `.env` en lugar de fiarte del valor por defecto, y consulta en Google AI Studio qué modelos hay disponibles.

> Estado de las pruebas: el proyecto se ha probado con Gemini (`gemini-3.5-flash-lite`). El modo Ollama está implementado, pero no se ha podido probar.

## Uso

```bash
python agente_graph.py
```

Al arrancar se crean las carpetas necesarias y tres archivos de prueba en `descargas/` (`prueba_tech.txt`, `prueba_deportes.txt`, `prueba_recetas.txt`). Después aparece el chat; escribe `salir` para terminar.

### Ejemplos de conversación

```
Usuario: Sube prueba_tech.txt y prueba_deportes.txt
Usuario: ¿Qué archivos hay en recepción?
Usuario: Guarda este texto como archivo: la bolsa y el euríbor suben
Usuario: Clasifica todos los archivos
Usuario: ¿Qué archivos hay en el tema deportes?
Usuario: ¿Y en finanzas?
```

## Herramientas MCP

| Herramienta | Descripción |
|---|---|
| `upload_file(filename)` | Copia un archivo de `descargas/` a `recepcion/` |
| `create_file_from_text(filename, content)` | Crea un archivo en `recepcion/` a partir de un texto |
| `list_recepcion_files()` | Lista los archivos pendientes en `recepcion/` |
| `read_file_content(filename)` | Devuelve el contenido de un archivo de `recepcion/` |
| `move_and_classify_file(filename, topic)` | Mueve un archivo a `clasificados/<tema>/` |
| `list_files_by_topic(topic)` | Lista los archivos ya clasificados en un tema |

El servidor valida los argumentos que envía el modelo: de los nombres de archivo solo conserva el nombre (se descartan rutas como `../../x`) y cualquier tema que no esté en la lista se trata como `otros`.

## Temas disponibles

`tecnologia`, `deportes`, `recetas`, `finanzas`, `otros`

Para añadir o quitar temas, edita la lista `TEMAS` en `agente_graph.py` **y** en `mcp_server.py` (deben coincidir).

## Limitaciones conocidas

- Solo procesa archivos de texto plano en UTF-8.
- Las rutas de las carpetas son relativas, por lo que el programa debe lanzarse desde la raíz del proyecto.
- El historial solo dura mientras la sesión está abierta; al cerrar el chat se pierde.
- Las carpetas de tema solo se crean cuando algún archivo se mueve a ellas, así que no existe `otros/` hasta que se clasifica algo en ese tema.
