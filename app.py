import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader

# 1. CONFIGURATION INTERFACE
st.set_page_config(page_title="Assistant Étudiant", layout="wide")
st.title("🎓 Assistant de Cours")

# 2. CONFIGURATION API
# On récupère la clé et on configure Google immédiatement
if "GEMINI_API_KEY" not in st.secrets:
    st.error("❌ Erreur : La clé 'GEMINI_API_KEY' est absente des Secrets Streamlit.")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# On force le modèle le plus commun
model = genai.GenerativeModel('gemini-1.5-flash')

# 3. GESTION DU DOCUMENT (BARRE LATÉRALE)
with st.sidebar:
    st.header("📁 Documents")
    uploaded_file = st.file_uploader("Uploader un PDF", type="pdf")
    
    if uploaded_file:
        reader = PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        st.session_state['document_text'] = text
        st.success("✅ Document chargé !")

# 4. GESTION DU CHAT
if "messages" not in st.session_state:
    st.session_state.messages = []

# Afficher l'historique
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Zone de saisie
if prompt := st.chat_input("Pose ta question..."):
    # Ajouter le message utilisateur
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Réponse de l'IA
    with st.chat_message("assistant"):
        if 'document_text' not in st.session_state:
            st.warning("Veuillez d'abord uploader un PDF.")
        else:
            try:
                # Création du contexte
                context = st.session_state['document_text'][:30000] # Limite à ~20 pages
                full_prompt = f"Voici un cours : {context}\n\nQuestion : {prompt}"
                
                # Appel direct à Google
                response = model.generate_content(full_prompt)
                
                # Affichage et sauvegarde
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                # Ici, on affiche l'erreur BRUTE pour comprendre le blocage
                st.error(f"Erreur Google : {str(e)}")
