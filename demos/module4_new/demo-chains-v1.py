from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
from langchain.chains import LLMChain
from LoadProperties import LoadProperties
from langchain_community.chat_models.oci_generative_ai import ChatOCIGenAI

#In this demo we will explore using LanChain Chain using chain class and a declarative approaches.

#Step 1 - setup OCI Generative AI llm

properties = LoadProperties()

llm = ChatOCIGenAI(
    model_id=properties.getModelName(),
    service_endpoint=properties.getEndpoint(),
    compartment_id=properties.getCompartment(),
    model_kwargs={"max_tokens":200}
)

#Step 2 - use chat messge template and messages and pass {question}

prompt = ChatPromptTemplate.from_messages([
    ("system", "You're a very knowledgeable scientist who provides accurate and eloquent answers to scientific questions."),
    ("human", "{question}")
])

#Step 3 - create a chain using LLMChain class and invoke a chain to get a response.
#legacy chain

#chain = LLMChain(llm=llm, prompt=prompt, output_parser=StrOutputParser())
#response = chain.invoke({"question":"What are basic elements of a matter"})
#print("Response from legacy chain")
#print(response)

#Step 4 - here we use langchain expression language to compose a chain and invoke it.
#lecl chain

runnable = prompt | llm | StrOutputParser()
response = runnable.invoke({"question": "What are basic elements of a matter"})
print("Response from LECL Chain")
print(response)




