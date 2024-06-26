import os

from dotenv import load_dotenv
from openai import OpenAI

from tools import Model

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_embedding(text, model=Model.EMBEDDING.value):
    return client.embeddings.create(
        input=text,
        model=model
    ).data[0].embedding
