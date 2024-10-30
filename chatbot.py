import streamlit as st
import pandas as pd
from sentence_transformers import SentenceTransformer, util
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.llms import Ollama
import sqlite3

# Connexion à la base de données SQLite
def connect_db():
    conn = sqlite3.connect('radeec.db')
    return conn

# Vérifier le numéro de compte et obtenir la consommation pour un mois spécifique
def check_account_and_get_consumption(numero_de_compte, mois):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT consommation FROM users WHERE numero_de_compte=? AND mois=?", (numero_de_compte, mois))
    result = cursor.fetchone()
    conn.close()
    if result:
        return result[0]
    return None

# Vérifier les factures
def check_facture(numero_de_compte, mois=None):
    conn = connect_db()
    cursor = conn.cursor()
    if mois:
        cursor.execute("SELECT mois, montant, statut, date_paiement FROM factures WHERE numero_de_compte=? AND mois=?", (numero_de_compte, mois))
    else:
        cursor.execute("SELECT mois, montant, statut, date_paiement FROM factures WHERE numero_de_compte=?", (numero_de_compte,))
    factures = cursor.fetchall()
    conn.close()
    return factures

# Charger et parser le dataset
def load_dataset(file_path):
    data = pd.read_csv(file_path)
    qa_pairs = {row['Question']: row['Réponse'] for _, row in data.iterrows()}
    return qa_pairs

# Obtenir la question la plus proche dans le dataset
def get_closest_question(question, qa_pairs, model):
    questions = list(qa_pairs.keys())
    question_embedding = model.encode(question, convert_to_tensor=True)
    question_embeddings = model.encode(questions, convert_to_tensor=True)
    cosine_scores = util.pytorch_cos_sim(question_embedding, question_embeddings)
    best_match_idx = cosine_scores.argmax().item()
    if cosine_scores[0, best_match_idx] > 0.7:  # Ajustez le seuil si nécessaire
        return questions[best_match_idx]
    return None

# Obtenir une réponse à partir du dataset ou de LLM
def get_response(question, qa_pairs, model):
    closest_question = get_closest_question(question, qa_pairs, model)
    if closest_question:
        return qa_pairs[closest_question]
    return "Désolé, je n'ai pas de réponse à cette question pour le moment."

# Configurer l'interface Streamlit
st.set_page_config(page_title="Chatbot RADEEC", page_icon=":droplet:", layout="wide")

# Styling avec du markdown
st.markdown("""
<style>
body {
    background-color: #f4f4f9;
    font-family: 'Arial', sans-serif;
}
.header {
    background-color: #003366;
    color: white;
    padding: 20px;
    text-align: center;
}
.title {
    font-size: 2.5em;
    margin-bottom: 0;
}
.subtitle {
    font-size: 1.2em;
}
.container {
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
    background-color: white;
    border-radius: 8px;
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
}
.message {
    padding: 10px;
    border-radius: 8px;
    margin-bottom: 10px;
}
.user-message {
    background-color: #e0f7fa;
    border-left: 5px solid #00acc1;
}
.chatbot-message {
    background-color: #f1f8e9;
    border-left: 5px solid #aed581;
}
</style>
""", unsafe_allow_html=True)

# En-tête et message de bienvenue
st.markdown("<div class='header'><div class='title'>Chatbot RADEEC</div><div class='subtitle'>Votre assistant pour toutes vos questions concernant l'eau</div></div>", unsafe_allow_html=True)

# Conteneur pour l'interface de chat
with st.container():
    st.write("Bonjour ! Posez votre question ci-dessous pour obtenir de l'aide.")
    
    # Charger le dataset
    dataset_path = "data_data.txt"  # Assurez-vous que le chemin est correct
    qa_pairs = load_dataset(dataset_path)

    # Charger le modèle d'encodage pour le français
    embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

    # Historique des conversations
    if 'history' not in st.session_state:
        st.session_state.history = []
    



# Ensemble de questions de référence pour chaque intention
intention_questions = {
    "consommation": ["Quelle est ma consommation pour ce mois ?", "Combien d'eau ai-je consommé ?", "Je veux voir ma consommation d'eau."],
    "facture": ["Montrez-moi mes factures", "Combien dois-je payer ?", "Je veux vérifier ma facture pour un certain mois."]
}

# Fonction pour détecter l'intention
def detect_intention(question, intention_questions, model):
    max_score = 0
    detected_intention = None
    question_embedding = model.encode(question, convert_to_tensor=True)
    
    for intention, examples in intention_questions.items():
        example_embeddings = model.encode(examples, convert_to_tensor=True)
        cosine_scores = util.pytorch_cos_sim(question_embedding, example_embeddings).max().item()
        if cosine_scores > max_score and cosine_scores > 0.75:  # Ajuster le seuil au besoin
            max_score = cosine_scores
            detected_intention = intention
    return detected_intention

# Modifications de la logique principale de Streamlit en fonction de l'intention détectée
with st.container():
    input_text = st.text_input("Posez votre question!", placeholder="Écrivez ici...")
    
    # Détecter l'intention de l'utilisateur
    if input_text:
        intention = detect_intention(input_text, intention_questions, embedding_model)
        
        # Vérification de la consommation
        if intention == "consommation":
            numero_de_compte = st.text_input("Veuillez entrer votre numéro de compte:", key="account_input")
            mois = st.text_input("Veuillez spécifier le mois (format AAAA-MM):", key="month_input")
            if st.button("Envoyer"):
                if numero_de_compte and mois:
                    consommation = check_account_and_get_consumption(numero_de_compte, mois)
                    response = f"Votre consommation pour le mois {mois} est de {consommation} m³." if consommation else "Le numéro de compte ou le mois est incorrect."
                    st.session_state.history.append({"role": "assistant", "content": response})
                else:
                    response = "Veuillez entrer un numéro de compte et une date valides."
                    st.session_state.history.append({"role": "assistant", "content": response})
        
        # Vérification des factures
        elif intention == "facture":
            numero_de_compte = st.text_input("Veuillez saisir votre numéro de compte pour voir vos factures :")
            if st.button("Voir les factures") and numero_de_compte:
                factures = check_facture(numero_de_compte)
                if factures:
                    st.write("Voici vos factures :")
                    for facture in factures:
                        mois, montant, statut, date_paiement = facture
                        response = f"Mois: {mois}, Montant: {montant} MAD, Statut: {statut}, Date de paiement: {date_paiement}"
                        st.session_state.history.append({"role": "assistant", "content": response})
                else:
                    response = "Aucune facture trouvée pour ce numéro de compte."
                    st.session_state.history.append({"role": "assistant", "content": response})
       
    

        # Autres questions générales
        else:
            submit_button = st.button("Envoyer")
            if submit_button:
                st.session_state.history.append({"role": "user", "content": input_text})
                response = get_response(input_text, qa_pairs, embedding_model)
                st.session_state.history.append({"role": "assistant", "content": response})





    
    # Afficher l'historique des conversations
    for msg in st.session_state.history:
        if msg["role"] == "user":
            st.markdown(f"<div class='message user-message'>{msg['content']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='message chatbot-message'>{msg['content']}</div>", unsafe_allow_html=True)

# Options supplémentaires dans la barre latérale
st.sidebar.title("Options supplémentaires")
st.sidebar.markdown("Consultez les sections suivantes pour plus d'informations :")
faq_questions = [
    "Comment puis-je consulter ma consommation d'eau ?",
    "Que faire en cas d'interruption de service ?",
    "Comment puis-je payer ma facture en ligne ?",
    "Comment souscrire à un nouveau service d'eau ?",
    "Comment signaler une fuite d'eau ?"
]
faq_answers = [
    "Vous pouvez consulter votre consommation d'eau en vous connectant à votre compte sur notre site web ou en utilisant notre application mobile.",
    "En cas d'interruption de service, veuillez vérifier notre site web ou notre application mobile pour des mises à jour. Vous pouvez également contacter notre service client pour plus d'informations.",
    "Vous pouvez payer votre facture en ligne via notre site web ou en utilisant notre application mobile.",
    "Pour souscrire à un nouveau service d'eau, veuillez remplir le formulaire de demande sur notre site web ou vous rendre dans notre agence la plus proche.",
    "Pour signaler une fuite d'eau, veuillez contacter notre service client immédiatement ou utiliser l'option de signalement dans notre application mobile."
]
for i, question in enumerate(faq_questions):
    if st.sidebar.button(question):
        st.session_state.history.append({"role": "user", "content": question})
        st.session_state.history.append({"role": "assistant", "content": faq_answers[i]})

st.sidebar.markdown('- [Contactez-nous](https://www.radeec.ma/contact/)')
st.sidebar.markdown("- [Télécharger notre application](#)")
