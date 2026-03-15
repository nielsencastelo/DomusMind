import json
from typing import Any

import requests
import streamlit as st

st.set_page_config(page_title="DomusMind", page_icon="🏠", layout="wide")

DEFAULT_API = "http://localhost:8000"
API_BASE_URL = st.sidebar.text_input("API base URL", value=DEFAULT_API)

st.title("DomusMind")
st.caption("Jarvis residencial com Streamlit + API + Home Assistant + câmera local")


def api_get(path: str) -> Any:
    response = requests.get(f"{API_BASE_URL}{path}", timeout=30)
    response.raise_for_status()
    return response.json()


def api_post(path: str, payload: dict) -> Any:
    response = requests.post(f"{API_BASE_URL}{path}", json=payload, timeout=180)
    response.raise_for_status()
    return response.json()


if "history" not in st.session_state:
    st.session_state.history = []

tab_chat, tab_config, tab_devices, tab_health = st.tabs(
    ["Assistente", "Configuração", "Dispositivos", "Saúde"]
)

with tab_chat:
    st.subheader("Conversa")
    user_text = st.text_area(
        "Comando",
        placeholder="Ex.: acenda a luz da sala / o que a câmera está vendo? / pesquise sobre Home Assistant",
        height=120,
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Enviar", use_container_width=True):
            if user_text.strip():
                with st.spinner("Processando..."):
                    result = api_post(
                        "/api/v1/chat",
                        {
                            "message": user_text,
                            "history": st.session_state.history,
                        },
                    )
                st.session_state.history = result["history"]
                st.success(result["response"])
                st.caption(
                    f"Intent: {result['intent']} | Provider: {result['provider_used']}"
                )

    with col2:
        if st.button("Falar última resposta", use_container_width=True):
            last_ai = next(
                (m for m in reversed(st.session_state.history) if m["role"] == "assistant"),
                None,
            )
            if last_ai:
                with st.spinner("Gerando áudio..."):
                    api_post("/api/v1/speech", {"text": last_ai["content"]})
                st.success("Resposta reproduzida.")

    with col3:
        if st.button("Limpar histórico", use_container_width=True):
            st.session_state.history = []
            st.success("Histórico limpo.")

    st.divider()
    st.subheader("Histórico")
    if not st.session_state.history:
        st.info("Nenhuma conversa ainda.")
    else:
        for item in st.session_state.history:
            speaker = "Você" if item["role"] == "user" else "DomusMind"
            st.markdown(f"**{speaker}:** {item['content']}")

with tab_config:
    st.subheader("rooms.json")
    try:
        config_data = api_get("/api/v1/config/rooms")
        edited = st.text_area(
            "Edite a configuração JSON",
            value=json.dumps(config_data, indent=2, ensure_ascii=False),
            height=500,
        )

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Salvar configuração", use_container_width=True):
                parsed = json.loads(edited)
                api_post("/api/v1/config/rooms", {"rooms": parsed})
                st.success("Configuração salva com sucesso.")

        with c2:
            if st.button("Recarregar", use_container_width=True):
                st.rerun()

    except Exception as exc:
        st.error(f"Erro ao carregar configuração: {exc}")

with tab_devices:
    st.subheader("Testes de dispositivos")

    d1, d2 = st.columns(2)

    with d1:
        st.markdown("### Home Assistant")
        room_name = st.text_input("Cômodo", value="sala", key="room_name")
        action = st.selectbox("Ação", ["on", "off"], key="light_action")

        if st.button("Testar luz", use_container_width=True):
            with st.spinner("Enviando comando..."):
                result = api_post(
                    "/api/v1/devices/light",
                    {"room": room_name, "action": action},
                )
            if result["ok"]:
                st.success(result["message"])
            else:
                st.error(result["message"])

    with d2:
        st.markdown("### Câmera")
        room_camera = st.text_input("Cômodo da câmera", value="escritorio", key="camera_room")
        if st.button("Testar captura/descrição", use_container_width=True):
            with st.spinner("Capturando e analisando..."):
                result = api_post("/api/v1/devices/vision", {"room": room_camera})
            st.write(result["description"])

with tab_health:
    st.subheader("Healthcheck")
    if st.button("Atualizar status", use_container_width=True):
        try:
            health = api_get("/api/v1/health")
            st.json(health)
        except Exception as exc:
            st.error(f"Erro no healthcheck: {exc}")