import streamlit as st
from mistralai import Mistral
from pypdf import PdfReader
import os

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Assistant Université 2026", layout="wide")
st.title("🎓 Chatbot des Étudiants")

# --- STYLE CSS AVANCÉ ---
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            /* Cache le bouton 'Deploy' et le menu en haut */
            .stAppDeployButton {display:none;}
            /* Cache l'ancre Streamlit en bas à droite sur certains navigateurs */
            .viewerBadge_container__1QSob {display:none !important;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# Sécurité Clé API
if "MISTRAL_API_KEY" not in st.secrets:
    st.error("❌ MISTRAL_API_KEY manquante dans les Secrets.")
    st.stop()

client = Mistral(api_key=st.secrets["MISTRAL_API_KEY"])
MODEL = "mistral-small-latest"

# --- 2. CHARGEMENT DU PDF (SANS UPLOAD) ---
PDF_PERMANENT = "Candidater.pdf"

@st.cache_resource
def charger_cours_permanent(file_path):
    if os.path.exists(file_path):
        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                content = page.extract_text()
                if content:
                    text += content + "\n"
            return text
        except Exception as e:
            return None
    return None

texte_universite = charger_cours_permanent(PDF_PERMANENT)

# --- 3. BARRE LATÉRALE ---
with st.sidebar:
    st.header("⚙️ Réglages de l'IA")
    temp = st.slider("Température", 0.0, 1.0, 0.2, step=0.1)
    top_p = st.slider("Top P", 0.0, 1.0, 0.9, step=0.1)
    max_t = st.number_input("Longueur réponse", 100, 2000, 600)
    
    st.divider()
    
    if st.button("🗑️ Vider la discussion"):
        st.session_state.messages = []
        st.rerun()

# --- 4. AFFICHAGE STATUT ---
if texte_universite:
    st.info(f"📚 Document chargé : {PDF_PERMANENT}")
else:
    st.error(f"⚠️ Erreur : Le fichier '{PDF_PERMANENT}' est introuvable sur GitHub.")

# --- 5. CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Posez votre question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if not texte_universite:
            st.error("Impossible de répondre car le document est absent.")
        else:
            try:
                with st.spinner("Analyse..."):
                    # On limite le contexte pour la rapidité
                    contexte_limite = texte_universite[:40000]
                    
                    full_prompt = f"Tu es un assistant. Réponds à la question avec ce texte :\n\n{contexte_limite}\n\nQuestion : {prompt}"
                    
                    chat_response = client.chat.complete(
                        model=MODEL,
                        messages=[{"role": "user", "content": full_prompt}],
                        temperature=temp,
                        top_p=top_p,
                        max_tokens=max_t
                    )
                    
                    response_text = chat_response.choices[0].message.content
                    st.markdown(response_text)
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
            except Exception as e:
                st.error(f"Erreur API : {e}")
