class LoadProperties:

    def __init__(self):

        import json
        # reading the data from the file
        with open('config.txt') as f:
            data = f.read()

        js = json.loads(data)

        self.model_name = js["model_name"]
        self.endpoint = js["endpoint"]
        self.compartment_ocid = js["compartment_ocid"]
        self.embedding_model_name=js["embedding_model_name"]
        self.langchain_key = js["langchain_key"]
        self.langchain_endpoint = js["langchain_endpoint"]

    def getModelName(self):
            return self.model_name

    def getEndpoint(self):
            return self.endpoint

    def getCompartment(self):
            return self.compartment_ocid

    def getEmbeddingModelName(self):
            return self.embedding_model_name

    def getLangChainKey(self):
            return self.langchain_key

    def getlangChainEndpoint(self):
            return self.langchain_endpoint











