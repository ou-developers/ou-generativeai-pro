import ads

ads.hello()

ads.set_auth(auth="api_key")
compartment_id="<<your compartment id>>"

from ads.llm import GenerativeAI

llm = GenerativeAI(
    compartment_id=compartment_id,
    # Optionally you can specify keyword arguments for the OCI client, e.g. service_endpoint.
    client_kwargs={
        "service_endpoint": "https://inference.generativeai.us-chicago-1.oci.oraclecloud.com"
    },
)

response = llm.invoke("Translate the following sentence into French:\nHow are you?\n")

print(response)
