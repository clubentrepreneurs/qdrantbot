import streamlit as st
from mistralai import Mistral
from pypdf import PdfReader
import os

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Assistant Université 2026", layout="wide")
st.title("🎓 Assistant Officiel des Étudiants")

if "MISTRAL_API_KEY" not in st.secrets:
    st.error("❌ MISTRAL_API_KEY manquante.")
    st.stop()

client = Mistral(api_key=st.secrets["MISTRAL_API_KEY"])
MODEL = "mistral-small-latest"

# --- 2. BARRE LATÉRALE : RÉGLAGES ---
with st.sidebar:
    st.header("⚙️ Réglages de l'IA")
    
    temp = st.slider("Température (Créativité)", 0.0, 1.0, 0.2, step=0.1)
    top_p = st.slider("Top P (Diversité)", 0.0, 1.0, 0.9, step=0.1)
    max_t = st.number_input("Longueur max réponse (Tokens)", 100, 2000, 600)

    st.divider()
    
    # Bouton pour vider le chat
    if st.button("🗑️ Réinitialiser la discussion"):
        st.session_state.messages = []
        st.rerun()

# --- 3. CHARGEMENT DU COURS PERMANENT ---
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

if texte_universite:
    st.info(f"📚 Base de connaissances active : {PDF_PERMANENT}")
else:
    st.error("⚠️ Fichier de cours introuvable sur le serveur.")

# --- 4. GESTION DU CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Pose ta question sur le document..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if not texte_universite:
            st.error("L'IA n'a pas accès au document source.")
        else:
            try:
                with st.spinner("Analyse..."):
                    contexte_limite = texte_universite[:45000]
                    
                    full_prompt = f"""Tu es un assistant pédagogique. 
                    Réponds à la question en utilisant UNIQUEMENT le texte suivant.
                    
                    TEXTE : {contexte_limite}
                    
                    QUESTION : {prompt}"""
                    
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
                st.error(f"Erreur : {str(e)}")
