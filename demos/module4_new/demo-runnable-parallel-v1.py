import ads
from langchain_core.runnables import RunnableParallel
from langchain_core.prompts import ChatPromptTemplate
from LoadProperties import LoadProperties

#In this demo we show how 2 chains can be run in parallel.
properties = LoadProperties()

ads.set_auth(auth="api_key")

from ads.llm import GenerativeAI

model = GenerativeAI(
    compartment_id=properties.getCompartment(),
    # Optionally you can specify keyword arguments for the OCI client, e.g. service_endpoint.
    client_kwargs={
        "service_endpoint": properties.getEndpoint()
    },
)

chain1 = ChatPromptTemplate.from_template("tell me a joke about {topic1}") | model
chain2 = ChatPromptTemplate.from_template("write a short (2 line) poem about {topic2}") | model

combined = RunnableParallel(joke=chain1, poem=chain2)

response = combined.invoke({"topic1":"pig","topic2":"parrot"})

print(response)
