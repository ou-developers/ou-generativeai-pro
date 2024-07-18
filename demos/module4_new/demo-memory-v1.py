from langchain.memory.buffer import ConversationBufferMemory
from langchain.memory import  ConversationSummaryMemory
from langchain.chains import LLMChain
from langchain.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain_community.chat_models.oci_generative_ai import ChatOCIGenAI
from LoadProperties import LoadProperties

#In this demo we will explore using LanChain Memory to store chat history

#Step 1 - setup OCI Generative AI llm

properties = LoadProperties()

# use default authN method API-key
llm = ChatOCIGenAI(
    model_id=properties.getModelName(),
    service_endpoint=properties.getEndpoint(),
    compartment_id=properties.getCompartment(),
    model_kwargs={"max_tokens":100}
)

#Step 2 - here we craete a Prompt
prompt = ChatPromptTemplate(
    messages=[
        SystemMessagePromptTemplate.from_template(
            "You are a nice chatbot who explain in steps."
        ),
        HumanMessagePromptTemplate.from_template("{question}"),
    ]
)

#Step 3 - here we create a memory to remember our chat with the llm

memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

summary_memory = ConversationSummaryMemory(llm=llm , memory_key="chat_history")

#Step 4 - here we create a conversation chain using llm , prompt and memory

conversation = LLMChain(llm=llm, prompt=prompt, verbose=True, memory=summary_memory)

#Step 5 - here we invoke a chain. Notice that we just pass in the `question` variables - `chat_history` gets populated by memory
conversation.invoke({"question": "What is the capital of India"})

#Step 6 - here we print all the messagess in the memory

print(memory.chat_memory.messages)
print(summary_memory.chat_memory.messages)
print("Summary of the conversation is-->"+summary_memory.buffer)

#Step 7 - here we ask a another question

conversation.invoke({"question": "what is oci data science certification?"})

#Step 8 - here we print all the messagess in the memory again and see that our last question and response is printed.
print(memory.chat_memory.messages)
print(summary_memory.chat_memory.messages)
print("Summary of the conversation is-->"+summary_memory.buffer)






