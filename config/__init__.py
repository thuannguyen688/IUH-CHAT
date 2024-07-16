import streamlit as st

QDRANT_CONFIG = {
    "URL": st.secrets["QDRANT"]["URL"],
    "API_KEY": st.secrets["QDRANT"]["API_KEY"]
}

MONGODB_CONFIG = {
    "URI": st.secrets["MONGODB"]["URI"],
    "DATABASE": st.secrets["MONGODB"]["DATABASE"],
    "CHAT_HISTORY": st.secrets["MONGODB"]["CHAT_HISTORY"],
    "LOGIN_HISTORY": st.secrets["MONGODB"]["LOGIN_HISTORY"],
    "BAN_COLLECTION": st.secrets["MONGODB"]["BAN_COLLECTION"],
    "ACCOUNT": st.secrets["MONGODB"]["ACCOUNT"],
    "CHAT_DB": st.secrets["MONGODB"]["CHAT_DB"]
}

MODEL_CONFIG = {
    "EMBEDDED": st.secrets["MODEL"]["EMBEDED"],
    "CHAT": st.secrets["MODEL"]["CHAT"],
    "API_KEY": st.secrets["MODEL"]["API_KEY"],
    "HUGGINGFACE": st.secrets["MODEL"]["HUGGINGFACE"]
}

LANGCHAIN = {
    "LANGCHAIN_ENDPOINT" : st.secrets["LANGCHAIN"]["LANGCHAIN_ENDPOINT"],
    "LANGCHAIN_API_KEY" : st.secrets["LANGCHAIN"]["LANGCHAIN_API_KEY"],
    "LANGCHAIN_PROJECT" : st.secrets["LANGCHAIN"]["LANGCHAIN_PROJECT"]
}


__all__ = ["QDRANT_CONFIG", "MONGODB_CONFIG", "MODEL_CONFIG", "LANGCHAIN"]