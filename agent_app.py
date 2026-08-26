"""
Agent Fichier — Interface Streamlit
Chat à gauche, panneau debug ingénieur à droite.
"""

import streamlit as st
from agent_core import run_agent, init_auth

# =============================================================================
# PAGE CONFIG
# =============================================================================
st.set_page_config(
    page_title="Agent Fichier",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =============================================================================
# CSS — Minimal + Debug panel styling
# =============================================================================
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container { padding-top: 1.5rem; }

    /* Debug panel — dark terminal aesthetic */
    .debug-box {
        background: #1E1E2E;
        color: #CDD6F4;
        border-radius: 8px;
        padding: 14px 16px;
        font-family: 'Cascadia Code', 'Fira Code', 'Consolas', monospace;
        font-size: 0.76rem;
        line-height: 1.7;
        height: 480px;
        overflow-y: auto;
        border: 1px solid #313244;
    }
    .debug-query {
        color: #89B4FA;
        font-weight: 700;
        border-bottom: 1px solid #313244;
        padding: 4px 0 6px 0;
        margin-top: 10px;
    }
    .debug-iter {
        color: #6C7086;
        font-style: italic;
        margin-top: 6px;
    }
    .dbg-thought { color: #F9E2AF; }
    .dbg-action  { color: #89DCEB; }
    .dbg-guard-ok { color: #A6E3A1; }
    .dbg-guard-ko { color: #F38BA8; }
    .dbg-error   { color: #F38BA8; font-weight: 600; }
    .dbg-result  { color: #CBA6F7; }
    .dbg-answer  { color: #A6E3A1; font-weight: 700; }
    .dbg-raw     { color: #585B70; font-size: 0.70rem; }
    .dbg-format  { color: #FAB387; }
    .dbg-idle    { color: #585B70; font-style: italic; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# SESSION STATE
# =============================================================================
if "messages" not in st.session_state:
    st.session_state.messages = []
if "debug_history" not in st.session_state:
    st.session_state.debug_history = []

# =============================================================================
# HEADER
# =============================================================================
st.markdown("# 🔍 Agent Fichier")
st.caption(
    "Assistant IA pour explorer et lire vos fichiers — "
    "Propulsé par votre LLM interne · Pattern ReAct"
)
st.markdown("")

# =============================================================================
# LAYOUT — 2 columns
# =============================================================================
col_chat, col_debug = st.columns([3, 2], gap="large")

import os
from path_guard import PathGuard

# ─── CHAT COLUMN ────────────────────────────────────────────
with col_chat:
    st.markdown("#### 💬 Conversation")
    
    # ── Upload Zone ──
    uploaded_file = st.file_uploader(
        "📥 Déposez un document pour que l'agent puisse l'analyser :", 
        type=["txt", "md", "csv", "docx", "xlsx"]
    )
    if uploaded_file is not None:
        guard = PathGuard()
        save_path = os.path.join(guard.root_dir, uploaded_file.name)
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success(f"Fichier `{uploaded_file.name}` ajouté au dossier de travail ! Demandez à l'agent de le lire.")

    # Scrollable chat container
    chat_container = st.container(height=460, border=True)
    with chat_container:
        if not st.session_state.messages:
            st.markdown(
                "👋 **Bonjour !** Demandez-moi d'explorer vos fichiers.\n\n"
                "Exemples :\n"
                "- *\"Liste les fichiers du dossier\"*\n"
                "- *\"Lis le fichier config.yaml\"*\n"
                "- *\"Qu'est-ce qu'il y a dans le dossier reports ?\"*"
            )
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # Chat input
    if prompt := st.chat_input("Posez votre question..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Run agent
        with st.spinner("🧠 L'agent réfléchit..."):
            auth = init_auth()
            answer, debug_logs = run_agent(
                prompt,
                st.session_state.messages[:-1],
                auth,
            )

        # Add assistant response
        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.session_state.debug_history.append({"query": prompt, "logs": debug_logs})
        st.rerun()

    # Clear button
    if st.button("🗑️ Effacer la conversation", use_container_width=True):
        st.session_state.messages.clear()
        st.session_state.debug_history.clear()
        st.rerun()


# ─── DEBUG COLUMN ────────────────────────────────────────────
with col_debug:
    st.markdown("#### 🔍 Panneau Ingénieur")

    if not st.session_state.debug_history:
        debug_html = (
            "<div class='debug-box'>"
            "<span class='dbg-idle'>⏳ En attente d'une requête...</span>"
            "</div>"
        )
    else:
        debug_html = "<div class='debug-box'>"

        for exchange in st.session_state.debug_history:
            # Query header
            q_safe = str(exchange["query"])[:80].replace("<", "&lt;").replace(">", "&gt;")
            debug_html += f"<div class='debug-query'>▶ {q_safe}</div>"

            for step in exchange.get("logs", []):
                # Iteration header
                it = step.get("iteration", "?")
                model = step.get("model", "")
                duration = step.get("duration", "")
                meta_parts = [f"Itération {it}"]
                if model:
                    meta_parts.append(model)
                if duration:
                    meta_parts.append(duration)
                debug_html += f"<div class='debug-iter'>── {' · '.join(meta_parts)} ──</div>"

                # Events
                for label, value in step.get("events", []):
                    safe_val = (
                        str(value)
                        .replace("<", "&lt;")
                        .replace(">", "&gt;")
                        .replace("\n", "<br>")
                    )

                    # Pick CSS class based on event type
                    if "THOUGHT" in label:
                        css = "dbg-thought"
                    elif "ACTION" in label:
                        css = "dbg-action"
                    elif "ALLOWED" in label or ("🛡️" in label and "✅" in label):
                        css = "dbg-guard-ok"
                    elif "BLOCKED" in label or "NOT FOUND" in label or ("🛡️" in label and "❌" in label):
                        css = "dbg-guard-ko"
                    elif "ERROR" in label or "❌" in label:
                        css = "dbg-error"
                    elif "RESULT" in label:
                        css = "dbg-result"
                    elif "ANSWER" in label:
                        css = "dbg-answer"
                    elif "FORMAT" in label or "⚠️" in label:
                        css = "dbg-format"
                    elif "RAW" in label:
                        css = "dbg-raw"
                    else:
                        css = "dbg-idle"

                    debug_html += f"<div class='{css}'>{label} {safe_val}</div>"

            debug_html += "<br>"

        debug_html += "</div>"

    st.markdown(debug_html, unsafe_allow_html=True)
