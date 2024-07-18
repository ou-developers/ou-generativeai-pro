from langchain.memory import ConversationBufferMemory
from langchain_community.chat_message_histories import StreamlitChatMessageHistory
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_community.chat_models.oci_generative_ai import ChatOCIGenAI
from LoadProperties import LoadProperties


#In this demo we will explore using Streamlit session to store chat messages


#Step 1 - setup OCI Generative AI llm

properties = LoadProperties()

# use default authN method API-key
llm = ChatOCIGenAI(
    model_id=properties.getModelName(),
    service_endpoint=properties.getEndpoint(),
    compartment_id=properties.getCompartment(),
    model_kwargs={"max_tokens":100}
)

#Step 2 - here we create a history with a key "chat_messages.

#StreamlitChatMessageHistory will store messages in Streamlit session state at the specified key=.
#A given StreamlitChatMessageHistory will NOT be persisted or shared across user sessions.

history = StreamlitChatMessageHistory(key="chat_messages")

#Step 3 - here we create a memory object

memory = ConversationBufferMemory(chat_memory=history)

#Step 4 - here we create template and prompt to accept a question

template = """You are an AI chatbot having a conversation with a human.
Human: {human_input}
AI: """
prompt = PromptTemplate(input_variables=["human_input"], template=template)

#Step 5 - here we create a chain object

llm_chain = LLMChain(llm=llm, prompt=prompt, memory=memory)

#Step 6 - here we use streamlit to print all messages in the memory, create text imput, run chain and
#the question and response is automatically put in the StreamlitChatMessageHistory

import streamlit as st

st.title('🦜🔗 Welcome to the ChatBot')
for msg in history.messages:
    st.chat_message(msg.type).write(msg.content)

if x := st.chat_input():
    st.chat_message("human").write(x)

    # As usual, new messages are added to StreamlitChatMessageHistory when the Chain is called.
    response = llm_chain.invoke(x)
    st.chat_message("ai").write(response["text"])





