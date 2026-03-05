import streamlit as st
from mistralai import Mistral
from pypdf import PdfReader
import os

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Assistant Université 2026", layout="wide", page_icon="🎓")

# --- STYLE CSS (Masquage total du header Streamlit) ---
hide_style = """
    <style>
    header {visibility: hidden !important;}
    [data-testid="stHeader"] {display: none !important;}
    [data-testid="stDecoration"] {display: none !important;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden !important;}
    .block-container {
        padding-top: 2rem; /* Un peu d'espace en haut pour respirer */
        padding-bottom: 0rem;
    }
    .stDeployButton {display:none;}
    </style>
    """
st.markdown(hide_style, unsafe_allow_html=True)

# --- TITRE POSITIONNÉ ---
st.markdown("<h1 style='text-align: center; margin-top: 0px;'>🎓 Assistant Officiel des Étudiants</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>Session 2026 - Guide des Candidatures</p>", unsafe_allow_html=True)
st.write("---")

# --- SÉCURITÉ API ---
if "MISTRAL_API_KEY" not in st.secrets:
    st.error("❌ MISTRAL_API_KEY manquante dans les Secrets.")
    st.stop()

client = Mistral(api_key=st.secrets["MISTRAL_API_KEY"])
MODEL = "mistral-small-latest"

# --- 2. CHARGEMENT DU PDF ---
PDF_PERMANENT = "Candidater.pdf"

@st.cache_resource
def charger_donnees(file_path):
    if os.path.exists(file_path):
        try:
            reader = PdfReader(file_path)
            nb_pages = len(reader.pages)
            text = ""
            for page in reader.pages:
                content = page.extract_text()
                if content:
                    text += content + "\n"
            return text, nb_pages
        except Exception:
            return None, 0
    return None, 0

texte_universite, pages_totales = charger_donnees(PDF_PERMANENT)

# --- 3. BARRE LATÉRALE ---
with st.sidebar:
    st.title("📂 Source Officielle")
    if texte_universite:
        st.success(f"**Fichier :** {PDF_PERMANENT}")
        st.info(f"📄 **{pages_totales} pages** analysées.")
        st.write("---")
    else:
        st.error("❌ Fichier source absent sur GitHub.")

    st.header("⚙️ Réglages IA")
    temp = st.slider("Précision / Créativité", 0.0, 1.0, 0.2)
    max_t = st.number_input("Longueur max réponse", 100, 2000, 600)
    
    if st.button("🗑️ Nouvelle conversation"):
        st.session_state.messages = []
        st.rerun()

# --- 4. CHAT ---
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
            st.error("Document source manquant.")
        else:
            try:
                with st.spinner("Analyse du document..."):
                    contexte = texte_universite[:45000]
                    system_prompt = "Tu es l'assistant de l'université. Réponds de manière claire et polie."
                    
                    response = client.chat.complete(
                        model=MODEL,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": f"Contexte: {contexte}\n\nQuestion: {prompt}"}
                        ],
                        temperature=temp,
                        max_tokens=max_t
                    )
                    
                    response_text = response.choices[0].message.content
                    st.markdown(response_text)
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
            except Exception as e:
                st.error(f"Erreur API : {e}")
