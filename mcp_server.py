import os
import shutil
from mcp.server.mcpserver import MCPServer

# Directorios base del proyecto
BASE_DIR = "./descargas"
RECEPCION_DIR = "./recepcion"
TOPICS_DIR = "./clasificados"

# Garantizar la existencia de los directorios iniciales
for directory in [BASE_DIR, RECEPCION_DIR, TOPICS_DIR]:
    os.makedirs(directory, exist_ok=True)

# Servidor MCP (compatible con MCP SDK 2.x)
mcp = MCPServer("ServidorArchivos")

@mcp.tool()
def upload_file(filename: str) -> str:
    """Simula la subida de un archivo desde la carpeta descargas hacia recepcion."""
    src = os.path.join(BASE_DIR, filename)
    dst = os.path.join(RECEPCION_DIR, filename)
    if not os.path.exists(src):
        return f"Error: El archivo '{filename}' no existe en {BASE_DIR}."
    shutil.copy2(src, dst)
    return f"Archivo '{filename}' copiado a recepción con éxito."

@mcp.tool()
def create_file_from_text(filename: str, content: str) -> str:
    """Guarda un texto introducido por el usuario directamente como archivo en recepción."""
    filepath = os.path.join(RECEPCION_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Archivo '{filename}' creado en recepción con éxito."

@mcp.tool()
def list_recepcion_files() -> str:
    """Lista todos los archivos pendientes de clasificación en la carpeta recepción."""
    files = os.listdir(RECEPCION_DIR)
    if not files:
        return "No hay archivos en la carpeta de recepción."
    return "Archivos en recepción: " + ", ".join(files)

@mcp.tool()
def read_file_content(filename: str) -> str:
    """Lee y devuelve el contenido de un archivo almacenado en recepción."""
    filepath = os.path.join(RECEPCION_DIR, filename)
    if not os.path.exists(filepath):
        return f"Error: El archivo '{filename}' no existe en recepción."
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

@mcp.tool()
def move_and_classify_file(filename: str, topic: str) -> str:
    """Mueve un archivo de recepción a la carpeta del tema especificado (crea la carpeta si no existe)."""
    src = os.path.join(RECEPCION_DIR, filename)
    if not os.path.exists(src):
        return f"Error: El archivo '{filename}' no existe en recepción."

    topic_folder = os.path.join(TOPICS_DIR, topic)
    os.makedirs(topic_folder, exist_ok=True)

    dst = os.path.join(topic_folder, filename)
    shutil.move(src, dst)
    return f"Archivo '{filename}' clasificado y movido a la carpeta '{topic}'."

@mcp.tool()
def list_files_by_topic(topic: str) -> str:
    """Lista todos los archivos almacenados bajo una carpeta de tema específica."""
    topic_folder = os.path.join(TOPICS_DIR, topic)
    if not os.path.exists(topic_folder) or not os.listdir(topic_folder):
        return f"No hay archivos en el tema '{topic}'."
    return f"Archivos en '{topic}': " + ", ".join(os.listdir(topic_folder))

if __name__ == "__main__":
    mcp.run()