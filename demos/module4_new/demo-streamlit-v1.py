import streamlit as st
#from langchain_community.llms import OCIGenAI
from langchain_community.chat_models.oci_generative_ai import ChatOCIGenAI
import oci
from LoadProperties import LoadProperties

#In this demo we will explore using Streamlit to input a question to llm and display the response

#Step 1 - setup OCI Generative AI llm
properties = LoadProperties()

# use default authN method API-key
llm = ChatOCIGenAI(
    model_id=properties.getModelName(),
    service_endpoint=properties.getEndpoint(),
    compartment_id=properties.getCompartment(),
    model_kwargs={"max_tokens":100}
)

#Step 2 - we define a function to return response

def generate_response(input_text):
  st.info(llm.invoke(input_text).content)

#Step 4 - here we write a quick streamlit application that accepts text input (question) and
# on clicking a 'submit button call a function that generates response

st.title('🦜🔗 Welcome to the ChatBot')
with st.form('my_form'):
  text = st.text_area('Enter text:', 'What are the three key pieces of advice for learning how to code?')
  submitted = st.form_submit_button('Submit')
  if submitted :
    generate_response(text)
