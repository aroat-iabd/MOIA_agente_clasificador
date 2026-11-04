# -*- coding: utf-8 -*-
from dotenv import load_dotenv
import os 
import os
from typing import TypedDict, Annotated
from dotenv import load_dotenv

from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI


load_dotenv()
GEMINI_API_KEY=os.getenv("GEMINI_API_KEY")


@tool
def calculator(expression: str) -> str:
    """Útil para realizar cálculos matemáticos exactos. Ingresa la expresión matemática."""
    try:
        result = eval(expression, {"__builtins__": None})
        return str(result)
    except Exception as e:
        return f"Error en el cálculo: {e}"


# EL ESTADO Y EL MODELO

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    next_agent: str 

#llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)
llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite")


# LOS NODOS

def nodo_enrutador(state: AgentState):
    """Analiza la petición y decide a qué agente enviarla."""
    mensaje_usuario = state["messages"][-1].content
    
    prompt = (
        "Eres un sistema de enrutamiento. Tu única tarea es clasificar el mensaje del usuario.\n"
        "Si el usuario pide cálculos, números o resolver problemas lógicos, responde: matematico\n"
        "Si el usuario pide escribir, rimas, literatura o algo creativo, responde: poeta\n\n"
        "Si el usuario pide chistes, bromas o algo divertido, responde: payaso\n"
        "Responde ÚNICAMENTE con una de esas tres palabras, en minúsculas y sin puntuación.\n"
        f"Mensaje: {mensaje_usuario}"
    )
    
    respuesta = llm.invoke(prompt)
    
    contenido = respuesta.content
    
    # Verificamos si Gemini nos ha devuelto una lista de bloques
    if isinstance(contenido, list):
        # Extraemos el texto del primer bloque
        if len(contenido) > 0 and isinstance(contenido[0], dict) and "text" in contenido[0]:
            texto = contenido[0]["text"]
        else:
            texto = str(contenido[0])
    else:
        # Si es un texto normal
        texto = str(contenido)
        
    destino = texto.strip().lower()

    
    # por seguridad, por lo que pueda devolver el llm
    if "matematico" in destino:
        destino = "matematico"
    elif "poeta" in destino:
        destino = "poeta"
    elif "payaso" in destino:
        destino = "payaso"
    else:
        destino = "poeta"  # Por defecto, si no se entiende, enviamos al poeta
        
    print(f" [Enrutador] Desviando consulta hacia: {destino.upper()}")
    
    return {"next_agent": destino}

def nodo_matematico(state: AgentState):
    """Es experto en números, tiene calculadora integrada)"""
    print("[Agente Matemático] calculando...")
    
    #Creamos un sub-agente exclusivo para este nodo, dándole la herramienta
    math_agent = create_react_agent(llm, tools=[calculator])
    
    #Definimos su personalidad (inyectada de forma segura para tu versión de LangGraph)
    prompt_sistema = SystemMessage(
        content="Eres un matemático brillante pero amable. "
                "USA OBLIGATORIAMENTE la herramienta 'calculator' para resolver la operación. "
                "Anima a la persona que te pregunta y siéntete agradecido por la oportunidad de ser útil."
    )
    
    #Preparamos los mensajes: Personalidad + Historial del usuario
    mensajes_para_agente = [prompt_sistema] + state["messages"]
    
    #Ejecutamos el sub-agente
    respuesta_sub_agente = math_agent.invoke({"messages": mensajes_para_agente})
    
    #Extraemos solo el mensaje final que nos dio el sub-agente para devolverlo al grafo principal
    respuesta_final = respuesta_sub_agente["messages"][-1]
    
    return {"messages": [respuesta_final]}

def nodo_poeta(state: AgentState):
    """Un experto en letras (Llamada simple, sin herramientas)."""
    print("[Agente Poeta] Recurriendo a las musas...")
    
    prompt_sistema = SystemMessage(
        content="Eres un poeta clásico y dramático del siglo XIX. "
                "Responde usando una poesía que rime. Usa palabras grandilocuentes."
    )
    
    # Como el poeta no necesita herramientas, hacemos un invoke() directo al LLM
    respuesta = llm.invoke([prompt_sistema] + state["messages"])
    
    return {"messages": [respuesta]}

def nodo_payaso(state: AgentState):
    """Un agente que hace bromas y chistes."""
    print("[Agente Payaso] Preparando chistes...")
    
    prompt_sistema = SystemMessage(
        content="Eres un payaso cómico y divertido. Responde con un chiste o broma graciosa."
    )
    
    respuesta = llm.invoke([prompt_sistema] + state["messages"])
    
    return {"messages": [respuesta]}


#  CONSTRUCCIÓN DEL GRAFO

grafo = StateGraph(AgentState)

grafo.add_node("enrutador", nodo_enrutador)
grafo.add_node("matematico", nodo_matematico)
grafo.add_node("poeta", nodo_poeta)
grafo.add_node("payaso", nodo_payaso)
grafo.add_edge(START, "enrutador")

def leer_decision(state: AgentState):
    return state["next_agent"]

grafo.add_conditional_edges(
    "enrutador",
    leer_decision,
    {
        "matematico": "matematico",
        "poeta": "poeta",
        "payaso": "payaso"
    }
)


grafo.add_edge("matematico", END)
grafo.add_edge("poeta", END)
grafo.add_edge("payaso", END)

app = grafo.compile()


# PRUEBILLAS

def hacer_pregunta(texto):
    print("\n")
    print(f"Usuario: {texto}")
    
    inputs = {"messages": [HumanMessage(content=texto)]}
    respuesta_final = app.invoke(inputs)
    print(f"Respuesta Final:\n{respuesta_final['messages'][-1].content}")


hacer_pregunta("¿Cuánto es 4567 multiplicado por 892?")
hacer_pregunta("Escríbeme un texto sobre la luna")
hacer_pregunta("Cuéntame un chiste sobre programadores")