import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
import os

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Assistant Étudiant Ultra-Stable", layout="wide")

try:
    GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=GEMINI_KEY)
except:
    st.error("⚠️ Clé API non trouvée dans les Secrets Streamlit.")
    st.stop()

# --- 2. INITIALISATION DU MODÈLE (TEST DE PLUSIEURS NOMS) ---
# On essaie de trouver un modèle disponible sur ton compte
@st.cache_resource
def load_stable_model():
    # Liste des noms possibles par ordre de préférence
    model_names = [
        'models/gemini-1.5-flash', 
        'gemini-1.5-flash', 
        'models/gemini-pro',
        'gemini-pro'
    ]
    
    for name in model_names:
        try:
            m = genai.GenerativeModel(name)
            # Test rapide pour voir si le modèle répond
            m.generate_content("test", generation_config={"max_output_tokens": 1})
            return m
        except:
            continue
    return None

model = load_stable_model()

if model is None:
    st.error("❌ Aucun modèle Gemini n'a pu être contacté. Vérifie ta clé API ou les restrictions de ton pays.")
    st.stop()

# --- 3. INTERFACE ---
st.title("🎓 Assistant de Cours (Version Stable)")

with st.sidebar:
    st.header("📁 Documents")
    uploaded_file = st.file_uploader("Uploader ton cours (PDF)", type="pdf")
    
    if uploaded_file:
        with st.spinner("Lecture du PDF..."):
            reader = PdfReader(uploaded_file)
            text_content = ""
            for page in reader.pages:
                text_content += page.extract_text()
            st.session_state['cours_texte'] = text_content
            st.success("Cours chargé avec succès !")

# --- 4. CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Pose ta question..."):
    if 'cours_texte' not in st.session_state:
        st.warning("Veuillez d'abord ajouter un PDF.")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                # On limite le texte pour ne pas saturer l'API (env. 15-20 pages)
                contexte = st.session_state['cours_texte'][:50000]
                
                instruction = f"""Tu es un tuteur académique. Utilise le texte suivant pour répondre à la question. 
                Si la réponse n'est pas dedans, utilise tes connaissances générales en le précisant.
                
                TEXTE DU COURS :
                {contexte}
                
                QUESTION :
                {prompt}"""
                
                response = model.generate_content(instruction)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Désolé, une erreur est survenue : {e}")
