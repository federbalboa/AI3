import os
import json
import datetime
import streamlit as st
from langchain_core.prompts import ChatPromptTemplate
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from agent.llm_setup import get_llm
from agent.skills import SKILLS_CONFIG
from utils.file_readers import read_all_files_in_folder
from agent.tools import agent_tools

def determine_skill(query: str, llm_type_override=None, ollama_model_override=None) -> str:
    llm = get_llm(llm_type_override, ollama_model_override)
    
    options = ""
    for skill_id, skill_info in SKILLS_CONFIG.items():
        options += f"- '{skill_id}': {skill_info['description']}\n"
        
    prompt = ChatPromptTemplate.from_template(
        "Eres un enrutador inteligente. Tu trabajo es analizar la pregunta del usuario y determinar qué skill (agente) debe responderla.\n\n"
        "Opciones disponibles:\n"
        "{options}\n\n"
        "Pregunta del usuario: {query}\n\n"
        "Responde ÚNICAMENTE con el ID del skill (ejemplo: finance, business_analyst o general). No agregues ninguna otra palabra ni explicación."
    )
    
    chain = prompt | llm
    
    try:
        result = chain.invoke({"options": options, "query": query}).content.strip().lower()
        if result in SKILLS_CONFIG:
            return result
        return "general"
    except Exception as e:
        print(f"Error en router: {e}")
        return "general"

def _try_execute_text_tool_calls(text: str) -> str | None:
    """Fallback: ejecuta tool calls que el modelo devolvió como texto suelto."""
    tool_names = [t.name for t in agent_tools]
    
    # Build description→name map for fuzzy matching
    desc_to_name = {}
    for t in agent_tools:
        desc_to_name[t.name.lower()] = t.name
        if t.description:
            desc_to_name[t.description.lower().strip().rstrip('.')] = t.name
            desc_to_name[t.description.lower().split('\n')[0].strip().rstrip('.')] = t.name

    def _resolve_tool_name(candidate: str) -> str | None:
        c = candidate.lower().strip()
        if c in desc_to_name:
            return desc_to_name[c]
        return None

    def _try_invoke_tool(name_str: str, params: dict) -> str | None:
        resolved = _resolve_tool_name(name_str)
        if not resolved:
            return None
        for tool in agent_tools:
            if tool.name == resolved:
                try:
                    return tool.invoke(params)
                except Exception as e:
                    return f"Error ejecutando {resolved}: {e}"
        return None

    # 0. Quick check: if the entire text is just a JSON tool call with no text around it, execute it directly
    stripped = text.strip()
    if stripped.startswith('{') and stripped.endswith('}'):
        try:
            obj = json.loads(stripped)
            if isinstance(obj, dict) and obj.get("name"):
                result = _try_invoke_tool(obj["name"], obj.get("parameters", {}))
                if result is not None:
                    return result
        except json.JSONDecodeError:
            pass

    # 1. Try JSON format
    try:
        obj = json.loads(text.strip())
        if isinstance(obj, dict) and "name" in obj:
            result = _try_invoke_tool(obj["name"], obj.get("parameters", {}))
            if result is not None:
                return result
        if isinstance(obj, list):
            results = []
            for item in obj:
                if isinstance(item, dict) and item.get("name"):
                    r = _try_invoke_tool(item["name"], item.get("parameters", {}))
                    if r:
                        results.append(r)
            if results:
                return "\n\n".join(results)
    except (json.JSONDecodeError, Exception):
        pass
    
    # Map old tool names to current names (backward compatibility)
    NAME_MAP = {'open_csv_in_visual_editor': 'open_table_editor'}

    # 2. Try pattern: tool_name(param1='val1', param2='val2')
    import re
    for tname in tool_names + list(NAME_MAP.keys()):
        actual_name = NAME_MAP.get(tname, tname)
        pattern = re.search(
            rf'{re.escape(tname)}\s*\(\s*(.*?)\s*\)',
            text, re.DOTALL
        )
        if pattern:
            args_str = pattern.group(1)
            kwargs = {}
            for match in re.finditer(r"""(\w+)\s*=\s*(?:'([^']*)'|"([^"]*)"|([^,)\s]+))""", args_str):
                key = match.group(1)
                val = match.group(2) or match.group(3) or match.group(4)
                kwargs[key] = val
            for tool in agent_tools:
                if tool.name == actual_name:
                    return tool.invoke(kwargs)
    
    # 3. Try pattern: tool_name key1=val1 key2=val2 (no parentheses)
    for tname in tool_names + list(NAME_MAP.keys()):
        actual_name = NAME_MAP.get(tname, tname)
        pattern = re.search(
            rf'{re.escape(tname)}\s+(\w+\s*=\s*[^\s,]+(?:\s+\w+\s*=\s*[^\s,]+)*)',
            text
        )
        if pattern:
            args_str = pattern.group(1)
            kwargs = {}
            for match in re.finditer(r"""(\w+)\s*=\s*(?:'([^']*)'|"([^"]*)"|([^\s,]+))""", args_str):
                key = match.group(1)
                val = match.group(2) or match.group(3) or match.group(4)
                kwargs[key] = val
            for tool in agent_tools:
                if tool.name == actual_name:
                    return tool.invoke(kwargs)
    
    return None

def execute_query(messages: list, llm_type_override=None, ollama_model_override=None, active_client="Chat General", progress_callback=None):
    try:
        return _execute_query_impl(messages, llm_type_override, ollama_model_override, active_client, progress_callback)
    except Exception as e:
        print(f"[ROUTER CATCHALL] execute_query error: {e}")
        return {"skill_name": "Agent", "skill_id": "general", "response": "Error al procesar la consulta. Por favor intenta de nuevo.", "folder_used": "data/general", "read_files": []}

def _execute_query_impl(messages: list, llm_type_override=None, ollama_model_override=None, active_client="Chat General", progress_callback=None):
    # Obtener el último mensaje del usuario para el enrutador
    latest_query = messages[-1]["content"] if messages else ""
    
    if progress_callback:
        progress_callback("🧠 Despertando a la IA y analizando intención...")
        
    # 1. Determinar el skill adecuado
    skill_id = determine_skill(latest_query, llm_type_override, ollama_model_override)
    skill = SKILLS_CONFIG.get(skill_id, SKILLS_CONFIG["general"])
    
    if progress_callback:
        progress_callback(f"🎯 Área de conocimiento asignada: {skill['name']}")
        progress_callback("📂 Buscando documentos relevantes...")
    
    # 2. Leer los documentos de la carpeta de clientes y la carpeta específica del skill
    read_files = []
    clients_path = os.path.join("data", "clientes")
    skill_context = read_all_files_in_folder(skill["folder"], progress_callback, read_files)
    
    # Obtener lista de carpetas de clientes existentes
    existing_clients = []
    if os.path.exists(clients_path):
        existing_clients = [d for d in os.listdir(clients_path) if os.path.isdir(os.path.join(clients_path, d))]
        
    if active_client != "Chat General" and active_client in existing_clients:
        specific_client_path = os.path.join(clients_path, active_client)
        clients_context = read_all_files_in_folder(specific_client_path, progress_callback, read_files)
        context_text = f"=== DATOS EXCLUSIVOS DEL CLIENTE ({active_client}) ===\n{clients_context}\n\n=== DATOS DEL SKILL ({skill['name']}) ===\n{skill_context}"
    else:
        # Optimización crítica: No leer todos los archivos en Chat General para evitar OOM (Out of Memory) en modelos locales
        clients_context = "Estás en el Chat General. Los datos profundos de los clientes están ocultos para ahorrar memoria. Pide al usuario que seleccione un cliente específico en la barra lateral si desea consultar sus archivos."
        context_text = f"=== LISTA DE CLIENTES ACTUALES ===\n{', '.join(existing_clients) if existing_clients else 'Ninguno'}\n\n=== DATOS DE TODOS LOS CLIENTES ===\n{clients_context}\n\n=== DATOS DEL SKILL ({skill['name']}) ===\n{skill_context}"
    
    # 3. Configurar el agente con herramientas
    llm = get_llm(llm_type_override, ollama_model_override)
    
    llm_prompt = (
        f"{skill['system_prompt']}\n\n"
        "Contexto extraído de documentos locales (PDF, DOCX, TXT, SQLite):\n"
        "=====================================\n"
        f"{context_text[:30000]}\n"
        "=====================================\n\n"
    )

    # Short-circuit greeting-only queries
    latest_query_text = messages[-1]["content"].strip().lower() if messages else ""
    greeting_words = ["hola", "buenas", "buenos", "hola!", "hola.", "qué tal", "como estás", "buen día", "buen dia", "saludos"]
    is_pure_greeting = any(latest_query_text == w or latest_query_text.startswith(w + " ") or latest_query_text.startswith(w + ",") for w in greeting_words)

    if is_pure_greeting:
        agent = create_react_agent(llm, tools=agent_tools, prompt=llm_prompt + "Responde solo con un saludo cálido y amigable. Nada más.")
    else:
        system_prompt = (
            llm_prompt +
            "Responde de forma natural y útil. Usa herramientas cuando necesites consultar o modificar datos.\n"
            "Herramientas disponibles: list_clients, create_client_folder, open_table_editor.\n"
            "NO generes funciones que no existen ni nombres inventados.\n"
            "EL SISTEMA USA SQLite. NO EXISTEN ARCHIVOS .csv.\n"
        )
        agent = create_react_agent(llm, tools=agent_tools, prompt=system_prompt)
    
    # Convertir el historial de dicts a objetos Message de LangChain
    chat_history = []
    for msg in messages:
        if msg["role"] == "user":
            chat_history.append(HumanMessage(content=msg["content"]))
        else:
            chat_history.append(AIMessage(content=msg["content"]))
            
    agent = create_react_agent(llm, tools=agent_tools, prompt=system_prompt)
    
    if progress_callback:
        progress_callback("🤖 Generando respuesta final (Esto puede tardar unos segundos)...")
        
    try:
        response = agent.invoke({
            "messages": chat_history
        })
    except Exception as e:
        error_str = str(e)
        print(f"[ROUTER DEBUG] agent.invoke error type={type(e).__name__}: {error_str[:300]}")
        return {
            "skill_name": skill["name"],
            "skill_id": skill_id,
            "response": f"Error de conexión con el proveedor de IA ({type(e).__name__}). Verifica tu clave API, conexión a internet, o cambia de proveedor en Ajustes.",
            "folder_used": f"data/clientes & {skill['folder']}",
            "read_files": read_files
        }

    try:
        output_content = response["messages"][-1].content

        if isinstance(output_content, list):
            text_parts = []
            for part in output_content:
                if isinstance(part, dict) and "text" in part:
                    text_parts.append(part["text"])
                elif isinstance(part, str):
                    text_parts.append(part)
            output_msg = "\n".join(text_parts)
        else:
            output_msg = str(output_content)

        # Only filter actual Gemini API errors, not generic text
        err_indicators = ["does not support image input", "inform the user",
                          "429 resource_exhausted", "quota exceeded for metric"]
        if any(indicator in output_msg.lower() for indicator in err_indicators):
            output_msg = "El servicio de IA respondió con un error. Intentá de nuevo o cambiá de proveedor en Ajustes."

        tool_result = _try_execute_text_tool_calls(output_msg)
        if tool_result is not None:
            output_msg = tool_result

        # If output is still just a bare JSON tool call that wasn't resolved, return a friendly message
        stripped = output_msg.strip()
        if stripped.startswith('{') and stripped.endswith('}') and '"name"' in stripped and '"parameters"' in stripped:
            import re
            name_match = re.search(r'"name"\s*:\s*"([^"]+)"', stripped)
            if name_match:
                tool_name = name_match.group(1)
                known = {t.name.lower(): t.name for t in agent_tools}
                if tool_name.lower() not in known:
                    output_msg = "¡Hola! Soy Agent 3000, tu asistente de gestión. Puedo mostrarte tus clientes, crear nuevos o abrir editores de datos. ¿En qué te puedo ayudar?"

        created_tables = st.session_state.get("agent_csv_files", [])
        all_data_sources = list(set(
            read_files +
            created_tables
        ))

        return {
            "skill_name": skill["name"],
            "skill_id": skill_id,
            "response": output_msg,
            "folder_used": f"data/clientes & {skill['folder']}",
            "read_files": all_data_sources
        }
    except Exception as e:
        return {
            "skill_name": "Error",
            "skill_id": "error",
            "response": f"Hubo un error al ejecutar el agente: {e}",
            "folder_used": "N/A",
            "read_files": []
        }
