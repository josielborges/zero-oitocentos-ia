import os

from dotenv import load_dotenv
from openai import OpenAI

from zero_oitocentos_api_consumer import get_task_to_ia, get_task_messages_to_ia

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

task_id = 987986
task_text = get_task_to_ia(task_id)
task_messages_text = get_task_messages_to_ia(task_id)

response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {
            "role": "system",
            "content": [
                {
                    "type": "text",
                    "text": '''
                            Você é um sistema que verifica dados de uma aplicação de helpdesk e deve analisar a
                            tarefa e como foi resolvida

                            Dada a tarefa e as providencias, retorne o problema da tarefa e como foi resolvida.

                            # Formato de saída (json com as informações abaixo):

                            numero: *id da tarefa*
                            titulo: *titulo da tarefa*
                            problema: *problema relatado na tarefa*
                            solucao: *texto da solução*

                            '''
                }
            ]
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f'''
                        Analise a tarefa {task_text}

                        As providencias são {task_messages_text}
                    '''
                }
            ]
        }
    ],
    temperature=1,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0
)

print(response.choices[0].message.content)
