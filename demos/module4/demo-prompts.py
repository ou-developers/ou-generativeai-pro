from langchain_core.prompts import PromptTemplate
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts import HumanMessagePromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage

from langchain_community.llms import OCIGenAI
import oci

#langchain.debug = True

#In this demo we will explore using LanChain Prompt templates


#Step 1 - setup OCI Generative AI llm

# Service endpoint
endpoint = "https://inference.generativeai.us-chicago-1.oci.oraclecloud.com"

# use default authN method
llm = OCIGenAI(
    model_id="cohere.command",
    service_endpoint="https://inference.generativeai.us-chicago-1.oci.oraclecloud.com",
    compartment_id="<<your compartment id>>",
    model_kwargs={"max_tokens":200}
)

#Step 2 - invoke llm with a fixed text input

response = llm.invoke("Tell me one fact about space", temperature=0.7)
print("Case1 Response - > "+ response)

#Step 3 - Use String Prompt to accept text input. Here we create a template and declare a input variable {human_input}

#String prompt

template = """You are a chatbot having a conversation with a human.
Human: {human_input} + {city}
:"""

#Step 4 - here we create a Prompt using the template

prompt = PromptTemplate(input_variables=["human_input", "city"], template=template)

prompt_val = prompt.invoke({"human_input":"Tell us in a exciting tone about", "city":"Las Vegas"})
print("Prompt String is ->")
print(prompt_val.to_string())

#Step 5 - here we declare a chain that begins with a prompt, next llm and finally output parser

chain = prompt | llm

#Step 6 - Next we invoke a chain and provide input question

response = chain.invoke({"human_input":"Tell us in a exciting tone about", "city":"Las Vegas"})

#Step 7 - print the prompt and response from the llm

print("Case2 Response - >" + response)


#Step 8 - Use Chat Message Prompt to accept text input. Here we create a chat template and use HumanMessage and SystemMessage

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a chatbot that explains in steps."),
        ("ai", "I shall explain in steps"),
        ("human", "{input}"),
    ]
)

chain = prompt | llm
response = chain.invoke({"input": "What's the New York culture like?"})
print("Case3 Response - > "+ response)

#Step10 - another example with .from_template()

prompt = ChatPromptTemplate.from_template("Tell me a joke about {animal}")
chain1 = prompt | llm
response = chain1.invoke({"animal": "zebra"})
print("Case4 Response - > "+ response)

#another example

chat_template = ChatPromptTemplate.from_messages(
    [
        SystemMessage(
            content=(
                "You are a helpful assistant that re-writes the user's text to "
                "sound more upbeat."
            )
        ),
        HumanMessagePromptTemplate.from_template("{text}"),
    ]
)

chain2 = chat_template | llm
response = chain2.invoke({"text":"I don't like eating tasty things"})
print("Case5 Response ->")

print(response)

