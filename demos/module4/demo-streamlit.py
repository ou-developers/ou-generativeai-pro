import streamlit as st
from langchain_community.llms import OCIGenAI
import oci

#In this demo we will explore using Streamlit to input a question to llm and display the response

#Step 1 - authenticate using "DEFAULT" profile

compartment_id = "ocid1.compartment.oc1..aaaaaaaah3o77etbcfg2o25jxks2pucmyrz6veg26z5lgpx3q355nikleemq"
CONFIG_PROFILE = "DEFAULT"
config = oci.config.from_file('~/.oci/config', CONFIG_PROFILE)

#Step 2 - setup OCI Generative AI llm

# Service endpoint
endpoint = "https://inference.generativeai.us-chicago-1.oci.oraclecloud.com"

# use default authN method API-key
llm = OCIGenAI(
    model_id="cohere.command-light",
    service_endpoint="https://inference.generativeai.us-chicago-1.oci.oraclecloud.com",
    compartment_id="ocid1.compartment.oc1..aaaaaaaah3o77etbcfg2o25jxks2pucmyrz6veg26z5lgpx3q355nikleemq",
    model_kwargs={"max_tokens":100}
)

#Step 3 - we define a function to return response

def generate_response(input_text):
  st.info(llm(input_text))

#Step 4 - here we write a quick streamlit application that accepts text input (question) and
# on clicking a 'submit button call a function that generates response

st.title('🦜🔗 Welcome to the ChatBot')
with st.form('my_form'):
  text = st.text_area('Enter text:', 'What are the three key pieces of advice for learning how to code?')
  submitted = st.form_submit_button('Submit')
  if submitted :
    generate_response(text)
