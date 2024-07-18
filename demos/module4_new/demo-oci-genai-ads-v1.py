import ads
from ads.llm import GenerativeAI
from LoadProperties import LoadProperties

ads.hello()

ads.set_auth(auth="api_key")

properties = LoadProperties()

llm = GenerativeAI(
    compartment_id=properties.getCompartment(),
    # Optionally you can specify keyword arguments for the OCI client, e.g. service_endpoint.
    client_kwargs={
        "service_endpoint": properties.getEndpoint()
    },
)

response = llm.invoke("Translate the following sentence into French:\nHow are you?\n")

print(response)
