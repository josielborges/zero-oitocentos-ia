import os

from dotenv import load_dotenv
from openai import OpenAI

from tools import Model

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

response = client.chat.completions.create(
    model=Model.GPT_3_5.value,
    messages=[
        {
            'role': 'user',
            'content': '''
                Imprima um Hello World criativo            
            '''

        }
    ]
)

print(response.choices[0].message.content)
