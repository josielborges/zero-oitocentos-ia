import html
import os
import re

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

# swagger https://servicos.fiescnet.com.br/swagger/ui/index
API_URL = 'https://servicos.fiescnet.com.br/api/'
API_TOKEN_URL = API_URL + 'seguranca/token'


def get_token():
    zo_user = os.getenv('ZERO_OITOCENTOS_API_USER')
    zo_password = os.getenv('ZERO_OITOCENTOS_API_PASSWORD')

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    cookies = {
        'CSScookieCSC': 'WS039'
    }
    data = {
        'grant_type': 'password',
        'username': zo_user,
        'password': zo_password
    }

    response = requests.post(API_TOKEN_URL, headers=headers, cookies=cookies, data=data)

    if response.status_code != 200:
        raise Exception(f'Error {response.status_code}: {response.text}')
    return response.json().get('access_token')


def get_task(task_id):
    headers = {
        'Authorization': 'Bearer ' + get_token()
    }
    response = requests.get(f'{API_URL}/tarefa/{task_id}', headers=headers)
    return response.json().get('titulo'), process_response(response.json().get('descricao'))


def get_messages(task_id):
    i = 1
    messages = []
    headers = {
        'Authorization': 'Bearer ' + get_token()
    }
    data_conclusao = ''
    while True:
        response = requests.get(f'{API_URL}/mob/providencia/tarefa/{task_id}/providencia/{i}', headers=headers)
        if response.status_code != 200:
            break
        messages.append(process_response(response.json().get('descricao')))
        data_conclusao = response.json().get('data')
        i += 1
    messages.append(f'----------\nData de conclusão: {data_conclusao}')
    return messages


def get_cleaned_text(text):
    cleaned_text = re.sub(r'\n+', '\n', text)
    cleaned_text = re.sub(r'\xa0+', '', cleaned_text)
    cleaned_text = re.sub(r'\ufeff+', '', cleaned_text)
    cleaned_text = cleaned_text.split('att')[0]
    cleaned_text = cleaned_text.split('Att')[0]
    cleaned_text = cleaned_text.split('Atenciosamente')[0]
    cleaned_text = cleaned_text.split('SENAI/SC - Soluções Digitais')[0]
    return cleaned_text


def process_response(response_text):
    soup = BeautifulSoup(html.unescape(response_text), 'html.parser')

    for div in soup.find_all("div"):
        div.insert(0, "\n")
        div.append("\n")

    return get_cleaned_text(soup.text)


def get_task_to_ia(task_id):
    task_title, task_text = get_task(task_id)
    text = f'Id da Tarefa: \n{task_id}\n'
    text += f'Título da Tarefa: \n{task_title}\n'
    text += f'Texto da Tarefa: {task_text}\n'
    return text


def get_task_messages_to_ia(task_id):
    text = ''
    i = 1
    for message in get_messages(task_id):
        text += f'Providência {i}:{message}'
        i += 1
    return text
