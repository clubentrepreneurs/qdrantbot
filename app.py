import streamlit as st
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import Qdrant
from langchain_text_splitters import RecursiveCharacterTextSplitter  # Corrigé précédemment
from langchain.chains.retrieval_qa.base import RetrievalQA           # Version stable pour ton code
from langchain_community.document_loaders import PyPDFLoader
import qdrant_client
import os

# 1. INIT & SÉCURITÉ
st.set_page_config(page_title="UniBot RAG", layout="wide")
GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
Q_URL = st.secrets["QDRANT_URL"]
Q_KEY = st.secrets["QDRANT_API_KEY"]

# Modèles
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=GEMINI_KEY)
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=GEMINI_KEY)

# 2. MOMENT DE L'INTÉGRATION DES FICHIERS (Interface Admin)
with st.sidebar:
    st.title("⚙️ Administration")
    uploaded_files = st.file_uploader("Ajouter des fichiers de cours (PDF)", type="pdf", accept_multiple_files=True)
    
    if uploaded_files and st.button("Indexer les documents"):
        for uploaded_file in uploaded_files:
            # Sauvegarde temporaire pour lecture
            with open(uploaded_file.name, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Chargement et découpage
            loader = PyPDFLoader(uploaded_file.name)
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            docs = loader.load_and_split(text_splitter)
            
            # Envoi vers Qdrant (C'est ici que les fichiers deviennent la base de savoir)
            Qdrant.from_documents(
                docs, embeddings, 
                url=Q_URL, api_key=Q_KEY, 
                collection_name="universite_savoir",
                force_recreate=False
            )
        st.success(f"{len(uploaded_files)} fichier(s) ajouté(s) au savoir du bot !")

# 3. INTERFACE ÉTUDIANT (Le Chat)
st.title("🎓 Assistant Étudiant Intelligent")
client = qdrant_client.QdrantClient(url=Q_URL, api_key=Q_KEY)
vectorstore = Qdrant(client=client, collection_name="universite_savoir", embeddings=embeddings)

if prompt := st.chat_input("Posez votre question sur les cours..."):
    with st.chat_message("user"):
        st.markdown(prompt)

    # RAG : Recherche dans les fichiers + Génération de réponse
    qa_chain = RetrievalQA.from_chain_type(
        llm, 
        retriever=vectorstore.as_retriever(),
        return_source_documents=True
    )
    
    with st.chat_message("assistant"):
        result = qa_chain.invoke(prompt)
        st.markdown(result["result"])
        
        # Affichage des sources pour éviter les hallucinations
        with st.expander("Sources consultées dans la documentation"):
            for doc in result["source_documents"]:
                st.write(f"- {doc.metadata['source']} (Page {doc.metadata.get('page',0)+1})")
