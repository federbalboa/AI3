import streamlit as st
import os
import re
import pandas as pd
from dotenv import load_dotenv, set_key
from agent.router import execute_query
from database import get_conn, read_table, write_table, ensure_table, list_tables, table_exists, find_or_create_table, migrate_all_csvs

env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
load_dotenv(dotenv_path=env_path, override=True)

migrate_all_csvs()

st.set_page_config(page_title="Agent 3000", page_icon="🤖", layout="wide")

# ── CSS: AI-Native UI (UX/UI Pro Max) ──────────────────────────────────
st.markdown(
    '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">'
    '<link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">',
    unsafe_allow_html=True
)

# ── CSS: AI-Native UI (UX/UI Pro Max) ──────────────────────────────────
st.markdown("""
<style>
* { font-family: "Inter", -apple-system, BlinkMacSystemFont, sans-serif; }
[data-testid="stIconMaterial"] { font-family: "Material Icons" !important; font-style: normal !important; font-weight: normal !important; }
#MainMenu, footer, .stAppDeployButton {display: none !important;}
header { background: transparent !important; border: none !important; }

/* ── App shell ── */
.stApp { background: #080c18; }
.main > .block-container { max-width: 920px; padding: 0.75rem 2rem 6rem; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1120 0%, #080c18 100%);
    border-right: 1px solid rgba(99,102,241,0.08);
    padding: 0.3rem 0.5rem;
}

/* ── Brand ── */
.sb-brand {
    display: flex; align-items: center; gap: 8px; padding: 4px 6px; margin-bottom: 0;
}
.sb-brand-icon {
    width: 28px; height: 28px; border-radius: 8px;
    background: linear-gradient(135deg, #6366f1, #4f46e5);
    display: flex; align-items: center; justify-content: center;
    font-size: 0.85rem; flex-shrink: 0;
}
.sb-brand-text {
    font-size: 0.85rem; font-weight: 700;
    background: linear-gradient(135deg, #a5b4fc, #6366f1);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; letter-spacing: -0.3px;
}
.sb-brand-sub {
    font-size: 0.55rem; color: #4a5578; letter-spacing: 1.5px; text-transform: uppercase;
    margin-top: -1px;
}

/* Section labels */
.sb-label {
    font-size: 0.6rem; color: #3a4466; font-weight: 600; letter-spacing: 0.8px;
    text-transform: uppercase; margin: 14px 8px 4px 8px;
}
[data-testid="stSidebar"] hr { border-color: rgba(99,102,241,0.05); margin: 8px 0; }

/* Quick action row */
.qact-grid { display: flex; gap: 4px; margin: 6px 0; }
.qact-grid .stButton > button {
    font-size: 0.7rem; font-weight: 500; padding: 3px 8px; height: 30px;
    border-radius: 6px; border: 1px solid rgba(99,102,241,0.08);
    background: rgba(99,102,241,0.04); color: #8892b0;
}
.qact-grid .stButton > button:hover {
    background: rgba(99,102,241,0.1); color: #c7d2fe; border-color: rgba(99,102,241,0.18);
}

/* Settings expander group */
.settings-group .streamlit-expanderHeader {
    font-size: 0.65rem; color: #5a6490; font-weight: 500;
    border-radius: 6px; padding: 4px 8px; margin: 2px 0;
}
.settings-group .streamlit-expanderContent { padding: 2px 4px; }

/* Sidebar footer */
.sb-footer {
    font-size: 0.6rem; color: #3a4466; text-align: center; padding: 8px; letter-spacing: 0.5px;
}

/* ── Top header ── */
.top-hdr {
    display: flex; align-items: center; justify-content: space-between;
    padding: 0.4rem 0 0.7rem 0; border-bottom: 1px solid rgba(99,102,241,0.06);
    margin-bottom: 0.5rem;
}
.top-hdr-left { display: flex; align-items: center; gap: 12px; }
.top-hdr-icon { display: flex; align-items: center; line-height: 1; }
.top-hdr-brand {
    font-size: 1.05rem; font-weight: 700;
    background: linear-gradient(135deg, #a5b4fc, #6366f1);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; letter-spacing: -0.4px;
}
.top-hdr-div { color: #2a3355; font-size: 0.75rem; margin: 0 2px; }
.top-hdr-ws { color: #94a3b8; font-size: 0.82rem; font-weight: 500; }

.top-hdr-right { display: flex; align-items: center; gap: 10px; }
.profile-chip {
    display: flex; align-items: center; gap: 8px; padding: 3px 10px 3px 3px;
    border-radius: 20px; background: rgba(99,102,241,0.06);
    border: 1px solid rgba(99,102,241,0.08); cursor: pointer; transition: all 0.15s ease;
}
.profile-chip:hover { background: rgba(99,102,241,0.12); }
.profile-avatar {
    width: 28px; height: 28px; border-radius: 50%;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    display: flex; align-items: center; justify-content: center;
    font-size: 0.65rem; font-weight: 700; color: #fff; flex-shrink: 0;
}
.profile-name { font-size: 0.78rem; color: #cbd5e1; font-weight: 500; line-height: 1.2; }
.profile-role { font-size: 0.62rem; color: #5a6490; line-height: 1; }

/* ── Empty state ── */
.empty-state { text-align: center; padding: 3.5rem 1.5rem 2rem; }
.empty-icon { margin-bottom: 0.7rem; opacity: 0.6; display: flex; justify-content: center; }
.empty-title { font-size: 1.3rem; font-weight: 600; color: #e2e8f0; margin-bottom: 0.4rem; }
.empty-sub { font-size: 0.82rem; color: #4a5578; margin-bottom: 1.5rem; }

.suggest-grid { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; max-width: 500px; margin: 0 auto; }
.suggest-chip {
    padding: 6px 16px; border-radius: 20px; font-size: 0.75rem;
    border: 1px solid rgba(99,102,241,0.12); background: rgba(99,102,241,0.04);
    color: #7a85b0; cursor: pointer; transition: all 0.2s ease;
}
.suggest-chip:hover { background: rgba(99,102,241,0.1); color: #c7d2fe; border-color: rgba(99,102,241,0.25); }

/* ── Chat messages ── */
[data-testid="stChatMessage"] { border: none; padding: 0.4rem 0; margin: 0; animation: msgIn 0.25s ease-out; }
@keyframes msgIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }

[data-testid="stChatMessage"] [data-testid="stChatMessageContent"] {
    background: transparent !important; padding: 0.3rem 0 !important;
    border: none !important; color: #e2e8f0; font-size: 0.88rem; line-height: 1.65;
}
[data-testid="stChatMessage"][data-testid="user"] [data-testid="stChatMessageContent"] {
    background: rgba(99,102,241,0.05) !important;
    border-radius: 14px !important; padding: 0.65rem 1rem !important;
    border: 1px solid rgba(99,102,241,0.08) !important;
}
[data-testid="stChatMessageAvatar"] { font-size: 1.3rem !important; line-height: 1; display: inline-flex !important; align-items: center; justify-content: center; }

/* ── Chat input (floating glass) ── */
[data-testid="stChatInput"] {
    position: fixed; bottom: 0; left: 50%; transform: translateX(-50%);
    width: min(700px, calc(100% - 3rem)); z-index: 100; padding: 0.8rem 0;
    background: linear-gradient(180deg, transparent 0%, #080c18 30%);
}
[data-testid="stChatInput"] > div {
    background: rgba(20,28,52,0.85) !important;
    backdrop-filter: blur(24px) !important;
    -webkit-backdrop-filter: blur(24px) !important;
    border: 1px solid rgba(99,102,241,0.12) !important;
    border-radius: 16px !important;
    padding: 0.2rem 0.2rem 0.2rem 1rem !important;
    box-shadow: 0 8px 32px rgba(0,0,0,0.3), inset 0 1px 0 rgba(99,102,241,0.05) !important;
}
[data-testid="stChatInput"] textarea {
    background: transparent !important; border: none !important;
    color: #e2e8f0 !important; font-size: 0.88rem !important; padding: 0.5rem 0 !important;
}
[data-testid="stChatInput"] textarea::placeholder { color: #4a5578 !important; }
[data-testid="stChatInput"] button {
    background: linear-gradient(135deg, #6366f1, #4f46e5) !important;
    border-radius: 12px !important; border: none !important; color: #fff !important;
    min-width: 38px !important; min-height: 38px !important;
    display: flex !important; align-items: center !important; justify-content: center !important;
    transition: all 0.2s ease !important;
}
[data-testid="stChatInput"] button:hover { transform: scale(1.05); box-shadow: 0 4px 20px rgba(99,102,241,0.35) !important; }
[data-testid="stChatInput"] button:disabled { background: rgba(99,102,241,0.15) !important; transform: none !important; box-shadow: none !important; }

/* ── Loading shimmer ── */
.shimmer-wrap {
    padding: 12px 16px; border-radius: 12px;
    background: rgba(30,41,59,0.3); border: 1px solid rgba(99,102,241,0.05);
    margin: 6px 0;
}
.shimmer-line {
    height: 12px; border-radius: 6px; margin-bottom: 8px;
    background: linear-gradient(90deg, rgba(99,102,241,0.04) 25%, rgba(99,102,241,0.1) 50%, rgba(99,102,241,0.04) 75%);
    background-size: 200% 100%; animation: shimmer 1.5s infinite;
}
.shimmer-line:last-child { width: 60%; margin-bottom: 0; }
.shimmer-line:nth-child(2) { width: 85%; }
@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }

/* ── Typing indicator ── */
.typing-dots { display: flex; gap: 4px; align-items: center; padding: 4px 0; }
.typing-dot {
    width: 6px; height: 6px; border-radius: 50%;
    background: #6366f1; animation: dotBounce 1.4s ease-in-out infinite;
}
.typing-dot:nth-child(2) { animation-delay: 0.2s; }
.typing-dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes dotBounce {
    0%, 60%, 100% { transform: translateY(0); opacity: 0.3; }
    30% { transform: translateY(-6px); opacity: 1; }
}

/* ── Status override ── */
.stStatusWidget {
    background: transparent !important; border: none !important;
    padding: 0 !important; margin: 0 !important;
}

/* ── Buttons ── */
.stButton > button {
    border-radius: 8px; font-size: 0.78rem; font-weight: 500;
    transition: all 0.15s ease;
    border: 1px solid rgba(99,102,241,0.1);
    background: rgba(99,102,241,0.04); color: #94a3b8;
}
.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(99,102,241,0.15);
    border-color: rgba(99,102,241,0.2); color: #cbd5e1;
}

/* ── Data editor ── */
[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; border: 1px solid rgba(99,102,241,0.08); }
[data-testid="stDataFrame"] thead tr th {
    background: rgba(99,102,241,0.06) !important; color: #818cf8 !important;
    font-size: 0.7rem !important; font-weight: 600 !important;
    text-transform: uppercase; letter-spacing: 0.5px; padding: 0.5rem 0.75rem !important;
}
[data-testid="stDataFrame"] tbody tr td {
    background: rgba(15,19,32,0.4) !important; color: #e2e8f0 !important;
    font-size: 0.78rem !important; padding: 0.4rem 0.75rem !important;
    border-bottom: 1px solid rgba(99,102,241,0.04) !important;
}

/* ── Select / Expander polish ── */
[data-testid="stSelectbox"] > div > div {
    background: rgba(20,28,52,0.6) !important;
    border: 1px solid rgba(99,102,241,0.08) !important;
    border-radius: 8px !important; color: #e2e8f0 !important;
}
.streamlit-expanderHeader {
    font-size: 0.75rem; color: #5a6490; border-radius: 8px;
}
[data-testid="stRadio"] { gap: 2px; padding: 0; }
[data-testid="stRadio"] label {
    font-size: 0.78rem !important; color: #8892b0 !important; padding: 2px 8px !important;
    border-radius: 6px; margin: 0; transition: all 0.15s ease;
}
[data-testid="stRadio"] label:hover { background: rgba(99,102,241,0.06); color: #c7d2fe !important; }
[data-testid="stRadio"] label > div:first-child { transform: scale(0.7); opacity: 0.5; }
[data-testid="stRadio"] label[data-checked="true"] {
    background: rgba(99,102,241,0.1) !important; color: #a5b4fc !important;
    font-weight: 500 !important;
}
[data-testid="stRadio"] label {
    padding: 5px 10px !important; border-radius: 6px !important;
    transition: all 0.12s ease;
}
[data-testid="stRadio"] label:hover { background: rgba(99,102,241,0.05); }

hr { border-color: rgba(99,102,241,0.05) !important; margin: 8px 0 !important; }
</style>
""", unsafe_allow_html=True)

# ── Init state ─────────────────────────────────────────────────────────
PROFILE_TABLE = find_or_create_table("user_profile", "Chat General", "Nombre,Rol,Departamento,Estado")
df_profile = read_table(PROFILE_TABLE)
if df_profile.empty:
    df_profile = pd.DataFrame([{"Nombre": "Usuario Admin", "Rol": "Director General", "Departamento": "Gerencia", "Estado": "Activo"}])
    write_table(PROFILE_TABLE, df_profile)

user_data = df_profile.iloc[0].to_dict() if not df_profile.empty else {"Nombre": "Desconocido", "Rol": "Usuario", "Departamento": ""}

clients_path = os.path.join("data", "clientes")
if os.path.exists(clients_path):
    client_folders = [d for d in os.listdir(clients_path) if os.path.isdir(os.path.join(clients_path, d))]
else:
    client_folders = []

if "_selected_workspace" not in st.session_state:
    st.session_state["_selected_workspace"] = "Chat General"

# ── Sidebar ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        "<div class='sb-brand'>"
        "<div class='sb-brand-icon'>"
        "<svg width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'>"
        "<circle cx='12' cy='12' r='3'/><path d='M12 1v4m0 14v4M1 12h4m14 0h4'/>"
        "</svg>"
        "</div>"
        "<div><div class='sb-brand-text'>Agent 3000</div><div class='sb-brand-sub'>Enterprise AI</div></div>"
        "</div>",
        unsafe_allow_html=True
    )

    st.markdown("<div class='sb-label'>Workspace</div>", unsafe_allow_html=True)
    ws_options = ["Chat General"] + client_folders
    selected_chat = st.radio(
        "",
        ws_options,
        index=ws_options.index(st.session_state["_selected_workspace"])
        if st.session_state["_selected_workspace"] in ws_options
        else 0,
        label_visibility="collapsed",
        key="workspace_radio"
    )
    st.session_state["_selected_workspace"] = selected_chat

    st.markdown("<div class='sb-label'>Acciones</div>", unsafe_allow_html=True)
    st.markdown("<div class='qact-grid'>", unsafe_allow_html=True)
    ca1, ca2 = st.columns(2)
    with ca1:
        if st.button("+ Cliente", use_container_width=True):
            st.session_state["show_add_client"] = True
            st.rerun()
    with ca2:
        if st.button("Perfil", use_container_width=True):
            st.session_state["pending_visual_edit"] = {"table_name": PROFILE_TABLE, "client_name": "Perfil de Usuario"}
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<div class='sb-label'>Herramientas</div>", unsafe_allow_html=True)
    if st.button("Ver Base de Datos", use_container_width=True):
        st.session_state["current_view"] = "database_browser"
        st.rerun()
    if st.session_state.get("current_view") == "database_browser":
        if st.button("Volver al Chat", use_container_width=True):
            st.session_state["current_view"] = "chat"
            st.rerun()

    if st.session_state.get("show_add_client"):
        with st.container(border=True):
            st.markdown("**Nuevo Cliente**")
            new_name = st.text_input("Nombre", key="new_client_name", placeholder="Nombre del cliente...")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Crear", use_container_width=True):
                    if new_name and new_name.strip():
                        name = new_name.strip()
                        client_path = os.path.join("data", "clientes", name)
                        os.makedirs(client_path, exist_ok=True)
                        from database import find_or_create_table, ensure_table
                        find_or_create_table("proyectos", name, "ID,Nombre_Proyecto,Descripcion,Monto_Estimado,Estatus,Fecha_Inicio")
                        find_or_create_table("informacion_general", name, "ID,Contacto,Email,Telefono,Direccion")
                        st.success(f"Cliente '{name}' creado.")
                        st.session_state["show_add_client"] = False
                        st.rerun()
            with c2:
                if st.button("Cancelar", use_container_width=True):
                    st.session_state["show_add_client"] = False
                    st.rerun()

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<div class='settings-group'>", unsafe_allow_html=True)
    with st.expander("Ajustes", expanded=False):
        with st.container():
            st.markdown("<div class='sb-label' style='margin-top:0'>Clientes</div>", unsafe_allow_html=True)
            if client_folders:
                for cf in sorted(client_folders):
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.caption(cf)
                    with c2:
                        if st.button("x", key=f"del_{cf}", help=f"Eliminar {cf}"):
                            import shutil
                            cf_path = os.path.join("data", "clientes", cf)
                            shutil.rmtree(cf_path, ignore_errors=True)
                            from database import get_conn, list_tables
                            prefix = 't_' + cf.lower().replace(' ', '_')
                            conn = get_conn()
                            cur = conn.cursor()
                            for tbl in list_tables(prefix):
                                cur.execute(f'DROP TABLE IF EXISTS "{tbl}"')
                            conn.commit()
                            conn.close()
                            if "chats" in st.session_state and cf in st.session_state.chats:
                                del st.session_state.chats[cf]
                            st.success(f"'{cf}' eliminado.")
                            st.rerun()
            else:
                st.caption("No hay clientes.")

            st.markdown("<div class='sb-label'>Engine</div>", unsafe_allow_html=True)
            env_llm = os.getenv("LLM_TYPE", "gemini").lower()
            options = ["gemini", "openai", "ollama"]
            default_idx = options.index(env_llm) if env_llm in options else 0
            selected_llm = st.selectbox("Proveedor", options, index=default_idx, label_visibility="collapsed")
            if selected_llm != env_llm:
                set_key(env_path, "LLM_TYPE", selected_llm)
                os.environ["LLM_TYPE"] = selected_llm
            ollama_model = None
            if selected_llm == "ollama":
                env_ollama_model = os.getenv("OLLAMA_MODEL", "llama3")
                ollama_model = st.text_input("Modelo", value=env_ollama_model)
                if ollama_model != env_ollama_model:
                    set_key(env_path, "OLLAMA_MODEL", ollama_model)
                    os.environ["OLLAMA_MODEL"] = ollama_model
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(f"<div class='sb-footer'>v2.0 &middot; {len(client_folders)} workspaces</div>", unsafe_allow_html=True)

# ── Top Header ──────────────────────────────────────────────────────────
st.markdown(
    f"<div class='top-hdr'>"
    f"<div class='top-hdr-left'>"
    f"<span class='top-hdr-icon'>"
    f"<svg width='22' height='22' viewBox='0 0 24 24' fill='none' stroke='#818cf8' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'>"
    f"<rect x='3' y='11' width='18' height='10' rx='2'/><circle cx='8.5' cy='16' r='1.5' fill='#818cf8'/>"
    f"<circle cx='15.5' cy='16' r='1.5' fill='#818cf8'/>"
    f"<path d='M12 3v8m-4-2l4-4 4 4'/></svg>"
    f"</span>"
    f"<span class='top-hdr-brand'>Agent 3000</span>"
    f"<span class='top-hdr-div'>/</span>"
    f"<span class='top-hdr-ws'>{'Base de Datos' if st.session_state.get('current_view') == 'database_browser' else selected_chat}</span>"
    f"</div>"
    f"<div class='top-hdr-right'>"
    f"<div class='profile-chip'>"
    f"<div class='profile-avatar'>{''.join([w[0] for w in user_data.get('Nombre', 'U').split()[:2]]).upper()}</div>"
    f"<div><div class='profile-name'>{user_data.get('Nombre', 'Usuario')}</div>"
    f"<div class='profile-role'>{user_data.get('Rol', '')}</div></div>"
    f"</div>"
    f"</div>"
    f"</div>",
    unsafe_allow_html=True
)

# ── Database Browser View ─────────────────────────────────────────────
if st.session_state.get("current_view") == "database_browser":
    from database import list_tables, read_table

    st.markdown("## Base de Datos")

    all_tables = list_tables()

    if not all_tables:
        st.info("No hay tablas en la base de datos.")
    else:
        tables_by_client = {}
        for t in sorted(all_tables):
            parts = t.replace('t_', '').split('_', 1)
            client = parts[0] if len(parts) > 1 else "General"
            if client not in tables_by_client:
                tables_by_client[client] = []
            tables_by_client[client].append(t)

        for client, tables in tables_by_client.items():
            with st.expander(f"{client} ({len(tables)} tablas)", expanded=True):
                for t in tables:
                    display = t.replace('t_', '').replace('_', ' ').title()
                    is_editing = st.session_state.get("db_editing_table") == t

                    c1, c2 = st.columns([4, 1])
                    with c1:
                        if is_editing:
                            st.markdown(f"**{display}** (editando)")
                        else:
                            st.markdown(f"**{display}**")
                    with c2:
                        if is_editing:
                            if st.button("Guardar", key=f"db_save_{t}"):
                                edit_df = st.session_state.get(f"db_df_{t}")
                                if edit_df is not None:
                                    write_table(t, edit_df)
                                    st.success(f"Guardado en {display}")
                                st.session_state["db_editing_table"] = None
                                st.rerun()
                        else:
                            if st.button("Editar", key=f"db_edit_{t}"):
                                st.session_state["db_editing_table"] = t
                                st.rerun()

                    try:
                        df = read_table(t)
                        if df.empty:
                            cols = [chr(65 + i) for i in range(5)]
                            df = pd.DataFrame({col: [''] for col in cols})
                        if is_editing:
                            col_list = list(df.columns)
                            df_vals = df.copy()
                            for c in col_list:
                                df_vals[c] = df_vals[c].astype(str)
                            edited = st.data_editor(df_vals, num_rows="dynamic", use_container_width=True, key=f"db_editor_{t}")
                            st.session_state[f"db_df_{t}"] = edited
                        else:
                            if not df.empty:
                                st.dataframe(df, use_container_width=True, hide_index=True)
                            else:
                                st.caption("(vacía)")
                    except Exception as e:
                        st.error(f"Error: {e}")
    st.stop()

# ── Chat History ────────────────────────────────────────────────────────
if "chats" not in st.session_state:
    st.session_state.chats = {}
if selected_chat not in st.session_state.chats:
    st.session_state.chats[selected_chat] = []

current_messages = st.session_state.chats[selected_chat]

# Empty state with suggestion chips
if not current_messages:
    st.markdown(
        "<div class='empty-state'>"
        "<div class='empty-icon'>"
        "<svg width='44' height='44' viewBox='0 0 24 24' fill='none' stroke='rgba(99,102,241,0.3)' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'>"
        "<rect x='3' y='11' width='18' height='10' rx='2'/><circle cx='8.5' cy='16' r='1.5' fill='rgba(99,102,241,0.3)'/>"
        "<circle cx='15.5' cy='16' r='1.5' fill='rgba(99,102,241,0.3)'/>"
        "<path d='M12 3v8m-4-2l4-4 4 4'/></svg>"
        "</div>"
        "<div class='empty-title'>En que puedo ayudarte?</div>"
        "<div class='empty-sub'>Selecciona un workspace o escribe una consulta para comenzar</div>"
        "<div class='suggest-grid'>"
        "<span class='suggest-chip' onclick='navigator.clipboard.writeText(\"Lista los clientes existentes\")'>Listar clientes</span>"
        "<span class='suggest-chip' onclick='navigator.clipboard.writeText(\"Agrega un nuevo cliente\")'>Agregar cliente</span>"
        "<span class='suggest-chip' onclick='navigator.clipboard.writeText(\"Que datos tienes?\")'>Que datos tienes?</span>"
        "<span class='suggest-chip' onclick='navigator.clipboard.writeText(\"Editar datos\")'>Editar datos</span>"
        "</div>"
        "</div>",
        unsafe_allow_html=True
    )

for message in current_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ── Chat Input ──
disable_chat = st.session_state.get("pending_visual_edit") is not None

if prompt := st.chat_input(f"Mensaje para {selected_chat}...", disabled=disable_chat):
    st.session_state.chats[selected_chat].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    st.session_state["agent_csv_files"] = []

    auto_table_before = None
    if re.search(r'\b(editar|edit|agregar|nuev[oa]|crear|modificar|cambi[ao]|insertar)\b', prompt, re.IGNORECASE):
        stem = f"{selected_chat}_datos" if selected_chat != "Chat General" else "general_data"
        auto_table_before = find_or_create_table(stem, selected_chat)

    with st.chat_message("assistant"):
        # Show shimmer + typing indicator while loading
        ph = st.empty()
        ph.markdown(
            "<div class='shimmer-wrap'>"
            "<div class='shimmer-line'></div>"
            "<div class='shimmer-line'></div>"
            "<div class='shimmer-line'></div>"
            "<div class='typing-dots' style='margin-top:8px'>"
            "<div class='typing-dot'></div><div class='typing-dot'></div><div class='typing-dot'></div>"
            "</div>"
            "</div>",
            unsafe_allow_html=True
        )

        def on_file_read(msg):
            pass

        contextual_messages = current_messages.copy()
        if selected_chat != "Chat General":
            last_user_msg = contextual_messages[-1].copy()
            last_user_msg["content"] = f"[CONTEXTO: Cliente '{selected_chat}']\n" + last_user_msg["content"]
            contextual_messages[-1] = last_user_msg

        try:
            result = execute_query(
                contextual_messages,
                llm_type_override=selected_llm,
                ollama_model_override=ollama_model,
                active_client=selected_chat,
                progress_callback=on_file_read
            )
        except Exception as e:
            print(f"[APP DEBUG] execute_query crashed: {e}")
            result = {
                "skill_name": "Agent",
                "response": "Error inesperado al conectar con el servicio de IA. Revisa los ajustes de conexión.",
                "read_files": []
            }

        skill_used = result.get("skill_name", "Desconocido")
        response_text = result.get("response", "")

        final_response = f"**{skill_used}**\n\n{response_text}"
        ph.markdown(final_response)
        st.session_state.chats[selected_chat].append({"role": "assistant", "content": final_response})

        data_sources = result.get("read_files", [])
        all_tables: list[str] = []

        for src in data_sources:
            if src.startswith('t_'):
                if src not in all_tables:
                    all_tables.append(src)
            elif src.lower().endswith('.csv'):
                stem = os.path.splitext(os.path.basename(src))[0]
                client = selected_chat if selected_chat != "Chat General" else "Chat General"
                tname = find_or_create_table(stem, client)
                if tname and tname not in all_tables:
                    all_tables.append(tname)

        text_tables = list(set(re.findall(r"t_[a-zA-Z_]+", response_text)))
        for tname in text_tables:
            if table_exists(tname) and tname not in all_tables:
                all_tables.append(tname)

        # Only show inline editor if user explicitly asked to edit/create/view table
        if st.session_state.get("pending_visual_edit"):
            pass  # handled below
        elif all_tables and auto_table_before:
            existing = st.session_state.get("editable_tables", [])
            st.session_state["editable_tables"] = list(set(existing + all_tables))
            first_table = all_tables[0]
            display_name = first_table.replace('t_', '', 1).replace('_', ' ').title()

            st.markdown(f"**{display_name}**")
            try:
                df = read_table(first_table)
                if df.empty:
                    cols = [chr(65 + i) for i in range(5)]
                    df = pd.DataFrame({col: [''] for col in cols})
                col_list = list(df.columns)
                df_vals = df.copy()
                for c in col_list:
                    df_vals[c] = df_vals[c].astype(str)
                edited_df = st.data_editor(df_vals, num_rows="dynamic", use_container_width=True, key=f"inline_editor_{first_table}")
                c1, c2 = st.columns([1, 8])
                with c1:
                    if st.button("Guardar", key=f"save_inline_{first_table}"):
                        write_table(first_table, edited_df)
                        st.success("Guardado!")
                        st.session_state.chats[selected_chat].append({"role": "user", "content": "Guardé los cambios en la tabla."})
                        st.session_state["pending_visual_edit"] = {"client_name": display_name, "table_name": first_table}
                        st.rerun()
                with c2:
                    if st.button("Cancelar", key=f"cancel_inline_{first_table}"):
                        st.session_state.chats[selected_chat].append({"role": "user", "content": "Cancelé la edición."})
                        st.session_state["pending_visual_edit"] = {"client_name": display_name, "table_name": first_table}
                        st.rerun()
            except Exception as e:
                st.error(f"Error al abrir editor: {e}")

# ── Top-level Editor ──
if st.session_state.get("pending_visual_edit"):
    edit_info = st.session_state["pending_visual_edit"]
    table_name = edit_info["table_name"]
    client_name = edit_info["client_name"]

    st.markdown(f"## {client_name}")
    try:
        df = read_table(table_name)
        if df.empty:
            cols = [chr(65 + i) for i in range(5)]
            df = pd.DataFrame({col: [''] for col in cols})
        col_list = list(df.columns)
        df_vals = df.copy()
        for c in col_list:
            df_vals[c] = df_vals[c].astype(str)
        edited_df = st.data_editor(df_vals, num_rows="dynamic", use_container_width=True)

        c1, c2 = st.columns([1, 8])
        with c1:
            if st.button("Guardar Cambios", key=f"save_top_{table_name}"):
                write_table(table_name, edited_df)
                st.success("Guardado!")
                st.session_state.chats[selected_chat].append({"role": "user", "content": "Guardé los cambios en la tabla."})
                st.session_state["pending_visual_edit"] = None
                st.rerun()
        with c2:
            if st.button("Cancelar", key=f"cancel_top_{table_name}"):
                st.session_state.chats[selected_chat].append({"role": "user", "content": "Cancelé la edición."})
                st.session_state["pending_visual_edit"] = None
                st.rerun()
    except Exception as e:
        st.error(f"Error: {e}")
        if st.button("Cerrar Editor"):
            st.session_state["pending_visual_edit"] = None
            st.rerun()
