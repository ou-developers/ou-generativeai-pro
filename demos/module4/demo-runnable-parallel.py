import ads
from langchain_core.runnables import RunnableParallel
from langchain_core.prompts import ChatPromptTemplate

ads.set_auth(auth="api_key")
compartment_id="<<your compartment id>>"

from ads.llm import GenerativeAI

model = GenerativeAI(
    compartment_id=compartment_id,
    # Optionally you can specify keyword arguments for the OCI client, e.g. service_endpoint.
    client_kwargs={
        "service_endpoint": "https://inference.generativeai.us-chicago-1.oci.oraclecloud.com"
    },
)

chain1 = ChatPromptTemplate.from_template("tell me a joke about {topic1}") | model
chain2 = ChatPromptTemplate.from_template("write a short (2 line) poem about {topic2}") | model

combined = RunnableParallel(joke=chain1, poem=chain2)

response = combined.invoke({"topic1":"pig","topic2":"parrot"})

print(response)
