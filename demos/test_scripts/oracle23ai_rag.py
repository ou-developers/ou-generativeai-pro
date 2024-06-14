import sys
import array
import time
import oci
import os
from dotenv import load_dotenv
from PyPDF2 import PdfReader
import oracledb
from sentence_transformers import CrossEncoder
from langchain.text_splitter import CharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores.utils import DistanceStrategy
from langchain_core.documents import BaseDocumentTransformer, Document
from langchain_community.llms import OCIGenAI
from langchain.llms import Cohere
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_community.vectorstores import oraclevs
from langchain_community.vectorstores.oraclevs import OracleVS
from langchain_community.embeddings import OCIGenAIEmbeddings
print("Successfully imported libraries and modules")

# Function to format and add metadata to Oracle 23ai Vector Store

def chunks_to_docs_wrapper(row: dict) -> Document:
    """
    Converts text into a Document object suitable for ingestion into Oracle Vector Store.
    - row (dict): A dictionary representing a row of data with keys for 'id', 'link', and 'text'.
    """
    metadata = {'id': str(row['id']), 'link': row['link']}
    print(metadata)
    return Document(page_content=row['text'], metadata=metadata)
print("Successfully defined metadata wrapper")

# Load environment variables

load_dotenv()
username = " "
password = " "
dsn = ''' '''

COMPARTMENT_OCID = " "
print("The database user name is:",username)
print("Database connection information is:",dsn)

# Connect to the database

try: 
    conn23c = oracledb.connect(user=username, password=password, dsn=dsn)
    print("Connection successful!")
except Exception as e:
    print("Connection failed!")


# RAG Step 1 - Load the document

# creating a pdf reader object
pdf = PdfReader('doc.pdf')

# print number of pages in pdf file 
print("The number of pages in this document is ",len(pdf.pages)) 
# print the first page 
print(pdf.pages[0].extract_text())

# RAG Step 2 - Transform the document to text

if pdf is not None:
  print("Transforming the PDF document to text...")
text=""
for page in pdf.pages:
    text += page.extract_text()
print("You have transformed the PDF document to text format")

# RAG Step 3 - Chunk the text document into smaller chunks
text_splitter = CharacterTextSplitter(separator="\n",chunk_size=800,chunk_overlap=100,length_function=len)
chunks = text_splitter.split_text(text)
print(chunks[0])

# Create metadata wrapper to store additional information in the vector store
"""
Converts a row from a DataFrame into a Document object suitable for ingestion into Oracle Vector Store.
- row (dict): A dictionary representing a row of data with keys for 'id', 'link', and 'text'.
"""
docs = [chunks_to_docs_wrapper({'id': page_num, 'link': f'Page {page_num}', 'text': text}) for page_num, text in enumerate(chunks)]
print("Created metadata wrapper with the chunks")

# RAG Step 4 - Using an embedding model, embed the chunks as vectors into Oracle Database 23ai.

# Initialize embedding model

model_4db = OCIGenAIEmbeddings(model_id=" ",service_endpoint=" ",compartment_id=" ")

print("check....Done")
# Configure the vector store with the model, table name, and using the indicated distance strategy for the similarity search and vectorize the chunks
s1time = time.time()
knowledge_base = OracleVS.from_documents(docs, model_4db, client=conn23c, table_name="MY_DEMO", distance_strategy=DistanceStrategy.DOT_PRODUCT)     
s2time =  time.time()  
print("check....Done")    
print( f"Vectorizing and inserting chunks duration: {round(s2time - s1time, 1)} sec.")

# Take a moment to celebrate. You have successfully uploaded the document, transformed it to text, split into chunks, and embedded its vectors in Oracle Database 23ai

print("Yay! You have successfully uploaded the document, transformed it to text, split into chunks, and embedded its vectors in Oracle Database 23ai")

# RAG Step 5 - Build the prompt to query the document

user_question = (" ")
print ("The prompt to the LLM will be:",user_question)


# Choice 1, Set the OCI GenAI LLM
ENDPOINT = " "
COMPARTMENT_OCID = COMPARTMENT_OCID
print(ENDPOINT)


cohere_api_key = " "

llmOCI = Cohere(
    model="command", 
    cohere_api_key=cohere_api_key, 
    max_tokens=1000, 
    temperature=0.7
)

# Set up the template for the questions and context, and instantiate the database retriever object
template = """Answer the question based only on the following context:
            {context} Question: {user_question}"""
prompt = PromptTemplate.from_template(template)
retriever = knowledge_base.as_retriever()

# RAG Steps 6 and 7 Chain the entire process together, retrieve the context, construct the prompt with the question and context, and pass to LLM for the response

s5time = time.time()
print("We are sending the prompt and RAG context to the LLM, wait a few seconds for the response...")
chain = (
  {"context": retriever, "user_question": RunnablePassthrough()}
     | prompt
     | llmOCI
     | StrOutputParser()
)
response = chain.invoke(user_question)
print(user_question)
print(response)
# Print timings for the RAG execution steps

s6time = time.time()
print("")
print( f"Send user question and ranked chunks to LLM and get answer duration: {round(s6time - s5time, 1)} sec.")

print("")
print("Congratulations! You've completed your RAG application with AI Vector Search in Oracle Database 23ai using LangChain")
