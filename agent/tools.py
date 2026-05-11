import os
from langchain_core.tools import tool
import streamlit as st
from database import ensure_table, write_table, read_table, find_or_create_table, list_tables
from utils.file_readers import read_all_files_in_folder

BASE_CLIENTS_DIR = os.path.join("data", "clientes")

@tool
def list_clients() -> str:
    """
    Lista TODOS los clientes (carpetas) existentes en el sistema con sus tablas SQLite.
    USA esta función cuando el usuario pregunte 'que clientes tengo', 'lista clientes', 'ver clientes'.
    """
    if not os.path.exists(BASE_CLIENTS_DIR):
        os.makedirs(BASE_CLIENTS_DIR)
        return "No hay clientes actualmente."

    clients = [d for d in os.listdir(BASE_CLIENTS_DIR) if os.path.isdir(os.path.join(BASE_CLIENTS_DIR, d))]
    if not clients:
        return "No hay clientes actualmente."

    result_text = f"Hay {len(clients)} clientes existentes:\n\n"
    all_tables = list_tables()
    for client in clients:
        result_text += f"=== CLIENTE: {client} ===\n"
        prefix = 't_' + client.lower().replace(' ', '_')
        client_tables = [t for t in all_tables if t.startswith(prefix)]
        if client_tables:
            for tbl in client_tables:
                df = read_table(tbl)
                if not df.empty:
                    result_text += f"Tabla '{tbl}':\n{df.to_string(max_rows=20)}\n\n"
                else:
                    result_text += f"Tabla '{tbl}' está vacía.\n"
        else:
            general_folder = os.path.join(BASE_CLIENTS_DIR, client, "general")
            if os.path.exists(general_folder):
                content = read_all_files_in_folder(general_folder)
                if content.strip():
                    result_text += f"Información en carpeta 'general':\n{content}\n"
        result_text += "\n"
    return result_text

@tool
def create_client_folder(client_name: str, initial_table_name: str = "datos_generales",
                         initial_headers: str = "ID,Nombre,Industria,Contacto,Email,Telefono,Observaciones") -> str:
    """
    Crea una nueva carpeta para un cliente y una tabla SQLite con las columnas especificadas.
    NO preguntes al usuario si quiere crearlo, solo créalo y confirma.
    Ejemplo: create_client_folder(client_name='FIN001', initial_table_name='contratos', initial_headers='ID,Cliente,Proyecto,Monto,Fecha')
    """
    client_path = os.path.join(BASE_CLIENTS_DIR, client_name)
    if not os.path.exists(client_path):
        try:
            os.makedirs(client_path)
        except Exception as e:
            return f"Error al crear la carpeta: {e}"

    table_name = find_or_create_table(initial_table_name, client_name, initial_headers)

    if "agent_csv_files" not in st.session_state:
        st.session_state.agent_csv_files = []
    st.session_state.agent_csv_files.append(table_name)

    return (f"Carpeta '{client_name}' creada/verificada. "
            f"Tabla '{table_name}' generada con columnas: {initial_headers}. El usuario ya puede editar los datos.")

@tool
def open_table_editor(client_name: str, table_name: str) -> str:
    """
    Abre un editor visual interactivo en la pantalla para que el usuario pueda ver y editar los datos de una tabla SQLite.
    Llama esta función SIEMPRE que el usuario pida editar, agregar o modificar datos.
    NO le pidas al usuario que escriba datos en el chat. Solo abre el editor.
    Ejemplo: open_table_editor(client_name='ControldeInsectos', table_name='contratos_servicio')
    """
    full_table = find_or_create_table(table_name, client_name)

    if not full_table.startswith('t_'):
        full_table = 't_' + full_table

    if "pending_visual_edit" not in st.session_state:
        st.session_state["pending_visual_edit"] = None

    st.session_state["pending_visual_edit"] = {
        "client_name": client_name,
        "table_name": full_table
    }

    return f"He abierto el editor visual para la tabla '{full_table}'. El usuario puede ver y editar los datos directamente en pantalla."

agent_tools = [list_clients, create_client_folder, open_table_editor]
