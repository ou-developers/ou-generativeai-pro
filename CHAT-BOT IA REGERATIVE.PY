!pip install nltk scikit-learn

import nltk
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

# Dados de exemplo (perguntas e respostas)
training_data = [
    ("Como você está?", "Eu estou bem, obrigado!"),
    ("Qual é o seu nome?", "Eu sou um chatbot."),
    ("O que você pode fazer?", "Eu posso responder perguntas e ajudar com informações."),
    ("Qual é a capital da França?", "A capital da França é Paris."),
    ("Quem é o presidente dos EUA?", "O presidente dos EUA é Joe Biden.")
]

# Separar perguntas e respostas
questions, answers = zip(*training_data)

# Inicializar o vetor de características e o classificador
model = Pipeline([
    ('vectorizer', CountVectorizer()),  # Convertendo texto para vetor
    ('classifier', MultinomialNB())      # Usando Naive Bayes para classificação
])

# Treinar o modelo
model.fit(questions, answers)

def chatbot_response(query):
    return model.predict([query])[0]

# Testar o chatbot
def chat():
    print("Digite 'sair' para encerrar o chat.")
    while True:
        user_input = input("Você: ")
        if user_input.lower() in ["sair", "exit"]:
            print("Chatbot: Até logo!")
            break
        response = chatbot_response(user_input)
        print(f"Chatbot: {response}")

# Execute a função de chat
chat()
