import streamlit as st
from mistralai import Mistral
from pypdf import PdfReader
import os

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Assistant Université 2026", layout="wide")
st.title("🎓 Assistant Officiel des Étudiants")

# Vérification de la clé API
if "MISTRAL_API_KEY" not in st.secrets:
    st.error("❌ MISTRAL_API_KEY manquante dans les Secrets Streamlit.")
    st.stop()

client = Mistral(api_key=st.secrets["MISTRAL_API_KEY"])
MODEL = "mistral-small-latest"

# --- 2. BARRE LATÉRALE : RÉGLAGES & DOCUMENTS ---
with st.sidebar:
    st.header("⚙️ Réglages de l'IA")
    
    # Paramètres de créativité (similaire à AnythingLLM)
    temp = st.slider("Température (Créativité)", 0.0, 1.0, 0.2, step=0.1, 
                     help="0.0 est factuel, 1.0 est très créatif.")
    top_p = st.slider("Top P (Diversité)", 0.0, 1.0, 0.9, step=0.1)
    max_t = st.number_input("Longueur max réponse (Tokens)", 100, 2000, 600)

    st.divider()
    
    st.header("📁 Administration")
    # Chargement automatique du cours permanent
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
                return f"Erreur de lecture : {e}"
        return None

    texte_universite = charger_cours_permanent(PDF_PERMANENT)

    # Option d'upload manuel pour tester d'autres fichiers
    uploaded_file = st.file_uploader("Mettre à jour le document (optionnel)", type="pdf")
    if uploaded_file:
        reader = PdfReader(uploaded_file)
        text_upload = ""
        for page in reader.pages:
            text_upload += page.extract_text() + "\n"
        st.session_state['document_text'] = text_upload
        st.info("Document temporaire chargé.")

    st.divider()
    
    # Bouton pour vider le chat
    if st.button("🗑️ Réinitialiser la discussion"):
        st.session_state.messages = []
        st.rerun()

# --- 3. AFFICHAGE STATUT ---
if texte_universite:
    st.success(f"📚 Base de connaissances chargée : {PDF_PERMANENT}")
else:
    st.warning("⚠️ Fichier 'Candidater.pdf' non trouvé à la racine du projet.")

# --- 4. GESTION DU CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Affichage de l'historique des messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Entrée utilisateur
if prompt := st.chat_input("Pose ta question sur le cours..."):
    # Ajouter le message utilisateur à l'historique
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Génération de la réponse
    with st.chat_message("assistant"):
        # Priorité au texte uploadé, sinon texte permanent
        context_final = st.session_state.get('document_text', texte_universite)
        
        if not context_final:
            st.error("Désolé, je n'ai aucune donnée (PDF) pour répondre.")
        else:
            try:
                with st.spinner("Analyse en cours..."):
                    # On limite le contexte pour éviter les coûts excessifs (~15-20 pages)
                    contexte_limite = context_final[:45000]
                    
                    full_prompt = f"""Tu es un assistant pédagogique universitaire. 
                    Utilise exclusivement le cours suivant pour répondre de manière précise.
                    Si la réponse n'est pas dans le texte, indique-le poliment.
                    
                    TEXTE DU COURS :
                    {contexte_limite}
                    
                    QUESTION :
                    {prompt}"""
                    
                    # Appel Mistral avec les paramètres personnalisés
                    chat_response = client.chat.complete(
                        model=MODEL,
                        messages=[{"role": "user", "content": full_prompt}],
                        temperature=temp,
                        top_p=top_p,
                        max_tokens=max_t
                    )
                    
                    response_text = chat_response.choices[0].message.content
                    st.markdown(response_text)
                    # Ajouter la réponse à l'historique
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
            except Exception as e:
                st.error(f"Erreur technique : {str(e)}")
