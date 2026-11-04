import os
import asyncio
from typing import Literal
from dotenv import load_dotenv  # <-- Cargar variables del .env

# Cargar las variables del archivo .env inmediatamente
load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langgraph.prebuilt.chat_agent_executor import create_react_agent
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# ==========================================
# 1. FUNCIÓN OBLIGATORIA: Selección de LLM
# ==========================================
def get_llm(provider: Literal["gemini", "ollama"] = "gemini", model_name: str = "gemini-1.5-flash"):
    """
    Fábrica de LLM para intercambiar modelos rápidamente entre Gemini y Ollama local.
    """
    if provider == "gemini":
        return ChatGoogleGenerativeAI(model=model_name, temperature=0.0)
    elif provider == "ollama":
        return ChatOllama(model=model_name, temperature=0.0)
    else:
        raise ValueError(f"Proveedor no soportado: {provider}")

# ==========================================
# 2. TEMAS PREFIJADOS Y SYSTEM PROMPT
# ==========================================
TEMAS = ["tecnologia", "deportes", "recetas", "finanzas", "otros"]
SYSTEM_PROMPT = f"""
Eres un agente organizador de archivos. TIENES PROHIBIDO inventar nombres de archivos o contenidos.
SIEMPRE debes ejecutar las herramientas reales para interactuar con el sistema de archivos.

Lista de temas prefijados: {', '.join(TEMAS)}.

Instrucciones de clasificación:
1. Revisa qué archivos hay en la carpeta de recepción ejecutando 'list_recepcion_files'.
2. Para cada archivo encontrado, lee su contenido con 'read_file_content'.
3. Clasifica el archivo basándote EXCLUSIVAMENTE en su contenido y asigna un tema de la lista de temas prefijados.
4. Mueve el archivo ejecutando 'move_and_classify_file'.
"""

# ==========================================
# 3. CONEXIÓN MCP Y EJECUCIÓN DEL GRAFO
# ==========================================
async def main():
    # Cambia 'provider="ollama"' y 'model_name="llama3.1"' si deseas probar localmente
    llm = get_llm(provider="gemini", model_name="gemini-1.5-flash")

    server_params = StdioServerParameters(
        command="python",
        args=["mcp_server.py"]
    )

    print("Iniciando conexión con el servidor MCP...")
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Declaración explícita de herramientas con firmas tipadas para LangChain
            @tool
            async def upload_file(filename: str) -> str:
                """Copia un archivo desde la carpeta descargas a recepción."""
                res = await session.call_tool("upload_file", arguments={"filename": filename})
                return "\n".join([c.text for c in res.content if hasattr(c, 'text')])

            @tool
            async def create_file_from_text(filename: str, content: str) -> str:
                """Crea un archivo en la carpeta recepción con el contenido especificado."""
                res = await session.call_tool("create_file_from_text", arguments={"filename": filename, "content": content})
                return "\n".join([c.text for c in res.content if hasattr(c, 'text')])

            @tool
            async def list_recepcion_files() -> str:
                """Lista todos los archivos pendientes en la carpeta recepción."""
                res = await session.call_tool("list_recepcion_files", arguments={})
                return "\n".join([c.text for c in res.content if hasattr(c, 'text')])

            @tool
            async def read_file_content(filename: str) -> str:
                """Lee el contenido de un archivo almacenado en recepción."""
                res = await session.call_tool("read_file_content", arguments={"filename": filename})
                return "\n".join([c.text for c in res.content if hasattr(c, 'text')])

            @tool
            async def move_and_classify_file(filename: str, topic: str) -> str:
                """Mueve un archivo de recepción a la carpeta del tema correspondiente."""
                res = await session.call_tool("move_and_classify_file", arguments={"filename": filename, "topic": topic})
                return "\n".join([c.text for c in res.content if hasattr(c, 'text')])

            @tool
            async def list_files_by_topic(topic: str) -> str:
                """Lista los archivos pertenecientes a un tema en la carpeta de clasificados."""
                res = await session.call_tool("list_files_by_topic", arguments={"topic": topic})
                return "\n".join([c.text for c in res.content if hasattr(c, 'text')])

            tools = [
                upload_file,
                create_file_from_text,
                list_recepcion_files,
                read_file_content,
                move_and_classify_file,
                list_files_by_topic,
            ]

            # Construcción del grafo ReAct
            agent_executor = create_react_agent(llm, tools)

            print("\n--- Agente Listo ---")
            print("Escribe 'salir' para terminar el chat.\n")

            while True:
                user_input = input("Usuario: ")
                if user_input.lower() in ['salir', 'exit', 'quit']:
                    break

                inputs = {
                    "messages": [
                        SystemMessage(content=SYSTEM_PROMPT),
                        HumanMessage(content=user_input)
                    ]
                }

                print("Agente pensando (ejecutando grafo)...")
                async for chunk in agent_executor.astream(inputs, stream_mode="values"):
                    last_message = chunk["messages"][-1]
                    if last_message.type == "ai" and not last_message.tool_calls:
                        print(f"Agente: {last_message.content}")

if __name__ == "__main__":
    # Preparación de la carpeta de descargas y archivos de prueba mínimos
    os.makedirs("./descargas", exist_ok=True)
    
    archivos_prueba = {
        "prueba_tech.txt": "python java código",
        "prueba_deportes.txt": "fútbol baloncesto gol",
        "prueba_recetas.txt": "tortilla patatas cebolla"
    }

    for nombre, contenido in archivos_prueba.items():
        ruta = os.path.join("./descargas", nombre)
        if not os.path.exists(ruta):
            with open(ruta, "w", encoding="utf-8") as f:
                f.write(contenido)

    asyncio.run(main())