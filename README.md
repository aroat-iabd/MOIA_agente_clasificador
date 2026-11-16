# MOIA – Agente clasificador de archivos

Agente conversacional que organiza archivos de texto por temas. Recibe archivos en una carpeta de **recepción**, lee su contenido, decide a qué tema pertenecen (tecnología, deportes, recetas, finanzas u otros) y los mueve a la carpeta correspondiente.

El agente está construido con **LangGraph** (agente ReAct) y accede al sistema de archivos a través de un servidor **MCP** (Model Context Protocol). El modelo de lenguaje es intercambiable entre **Google Gemini** (en la nube) y **Ollama** (local).

## Cómo funciona

```
Usuario ──► agente_graph.py (LangGraph + LLM)
                 │  cliente MCP (stdio)
                 ▼
            mcp_server.py ──► descargas/ ──► recepcion/ ──► clasificados/<tema>/
```

1. `agente_graph.py` arranca el servidor MCP como subproceso y se conecta a él por stdio.
2. Las herramientas del servidor se exponen al agente como *tools* de LangChain.
3. El usuario chatea con el agente por consola. Para clasificar, el agente:
   1. lista los archivos de `recepcion/`,
   2. lee el contenido de cada uno,
   3. elige un tema de la lista prefijada basándose solo en el contenido,
   4. mueve el archivo a `clasificados/<tema>/`.

## Estructura del proyecto

```
MOIA_agente_clasificador/
├── agente_graph.py     # Agente LangGraph, selección de LLM y chat por consola
├── mcp_server.py       # Servidor MCP con las herramientas de archivos
├── requirements.txt    # Dependencias
├── .env                # Tu API key (no se sube a git)
├── .env.example        # Plantilla de variables de entorno
├── .gitignore
├── descargas/          # Origen simulado de archivos (se crea solo)
├── recepcion/          # Archivos pendientes de clasificar (se crea solo)
└── clasificados/       # Resultado: una subcarpeta por tema (se crea sola)
```

## Requisitos

- Python 3.10 o superior
- Una API key de Google Gemini (si usas Gemini) **o** [Ollama](https://ollama.com) instalado con un modelo descargado (si usas el modo local)

## Instalación

Desde la carpeta del proyecto (Windows, PowerShell):

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

## Configuración

Copia la plantilla y rellena tu clave:

```powershell
copy .env.example .env
```

Contenido de `.env`:

```
GEMINI_API_KEY=tu_api_key
```

> No subas nunca el archivo `.env` a git ni lo compartas. Ya está incluido en `.gitignore`.

### Elegir el modelo

La función `get_llm()` de `agente_graph.py` permite cambiar de proveedor:

```python
llm = get_llm(provider="gemini", model_name="gemini-2.5-flash")  # nube
llm = get_llm(provider="ollama", model_name="llama3.1")          # local
```

Para usar Ollama, asegúrate de tener el servicio en marcha y el modelo descargado (`ollama pull llama3.1`). El modelo debe soportar *tool calling*.

## Uso

```bash
python agente_graph.py
```

Al arrancar se crean las carpetas necesarias y tres archivos de prueba en `descargas/` (`prueba_tech.txt`, `prueba_deportes.txt`, `prueba_recetas.txt`). Después aparece el chat; escribe `salir` para terminar.

### Ejemplos de conversación

```
Usuario: Sube prueba_tech.txt y prueba_deportes.txt y clasifícalos
Usuario: Crea un archivo notas.txt con el texto "el euríbor sube y los bancos suben tipos" y clasifícalo
Usuario: Clasifica todo lo que haya en recepción
Usuario: ¿Qué archivos hay en el tema deportes?
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

## Temas disponibles

`tecnologia`, `deportes`, `recetas`, `finanzas`, `otros`

Para añadir o quitar temas, edita la lista `TEMAS` en `agente_graph.py`.

## Limitaciones conocidas

- Solo procesa archivos de texto en UTF-8.
- Las rutas de las carpetas son relativas, por lo que el programa debe lanzarse desde la raíz del proyecto.
