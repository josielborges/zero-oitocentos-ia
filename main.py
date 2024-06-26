import json
import os
import re

import numpy as np
from dotenv import load_dotenv
from openai import OpenAI
from sklearn.metrics.pairwise import cosine_similarity

from ellevo_api_consumer import get_task_to_ia, get_task_messages_to_ia
from embbeding_utils import generate_embedding
from tools import save, load

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

EMBEDDINGS_PATH = "data/embeddings/"
TASKS_FILES_PATH = "data/tasks_files/"


def get_task_content(task_id):
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
                        'text': '''
                            Objetivo: Avaliar e extrair informações de tarefas resolvidas de um programa de helpdesk.
    
                            Instruções:
                            1. Avalie cada tarefa resolvida.
                            2. Identifique e extraia os seguintes elementos:
                               - Número da Tarefa: Identifique o número da tarefa.
                               - Título da Tarefa: Identifique o título da tarefa.
                               - Problema: Analise o texto da tarefa e descreva qual era o problema relatado.
                               - Solução: Examine a lista de providências e identifique como o problema foi resolvido. Descreva as atividades realizadas que levaram à resolução do problema.
                               - Data de Conclusão: Identifique a data de conclusão da tarefa (geralmente presente nas providências).
                            
                            3. Apresente os resultados no formato JSON especificado abaixo para cada tarefa avaliada.
    
                            Formato de saída para cada tarefa em JSON:
                            {
                              "numeroTarefa": "[Número da Tarefa]",
                              "tituloTarefa": "[Título da Tarefa]",
                              "problema": "[Descrição do Problema]",
                              "solucao": "[Descrição da Solução]",
                              "dataConclusao": "[Data de Conclusão no formato YYYY-MM-DD]"
                            }
                            
                            Exemplo de saída:
                            {
                              "numeroTarefa": "12345",
                              "tituloTarefa": "Computador não liga",
                              "problema": "O usuário relatou que o computador não liga após apertar o botão de power.",
                              "solucao": "Foi verificado o cabo de alimentação e substituído por um novo. O computador ligou normalmente após a substituição do cabo.",
                              "dataConclusao": "2024-06-20"
                            }
                            
                            Por favor, processe as tarefas resolvidas e forneça os resultados conforme o formato JSON acima.
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

    return response.choices[0].message.content


def get_all_embeddings():
    embeddings = []
    filenames = []
    for embedding_file in os.listdir(EMBEDDINGS_PATH):
        with open(f"{EMBEDDINGS_PATH}{embedding_file}", 'r') as file:
            file_content = file.read()
            # Converte a string do arquivo para uma lista de floats
            embedding = np.array(eval(file_content))
            embeddings.append(embedding)
            filenames.append(embedding_file)
    return embeddings, filenames


def find_similarities(question):
    question_embeddings = np.array(generate_embedding(question))
    all_embeddings, filenames = get_all_embeddings()
    all_embeddings = np.array(all_embeddings)

    similarities = cosine_similarity([question_embeddings], all_embeddings)
    top_most_similar_index = np.argsort(similarities[0])[-10:][::-1]

    top_similar_file_names = []
    top_similar_scores = []
    for index in top_most_similar_index:
        if similarities[0][index] > 0.5:
            top_similar_file_names.append(filenames[index])
            top_similar_scores.append(similarities[0][index])

    return top_similar_file_names, top_similar_scores


def generate_embeddings(tasks):
    i = 1
    count = len(tasks)
    for task in tasks:
        print(f'Gerando embedding para {task} ({i} de {count}, {i / count * 100:.2f}%)')
        task_content = get_task_content(task)
        print(task_content)
        save(f'{TASKS_FILES_PATH}{task}.txt', task_content)
        i += 1


def generate_embeddings_problem_only():
    i = 1
    count = len(os.listdir(TASKS_FILES_PATH))
    for file in os.listdir(TASKS_FILES_PATH):
        print(f'Gerando embedding para {file.split('.')[0]} ({i} de {count}, {i / count * 100:.2f}%)')
        if file.endswith(".txt"):
            if os.path.exists(f'data/embeddings/{file}'):
                print("Já existe embedding pra esse arquivo")
                i += 1
                continue
            content = load(f'{TASKS_FILES_PATH}cleaned/{file}')
            title_and_problem = extract_title_and_problem_from_task_text(content)
            print(title_and_problem)
            embeddings = generate_embedding(title_and_problem)
            save(f'data/embeddings/{file}', str(embeddings))
        i += 1


def extract_title_and_problem_from_task_text(task_text):
    print(task_text)
    return (f'{json.loads(task_text).get('tituloTarefa')}\n'
            f'{json.loads(task_text).get('problema')}')


def generate_recomendation(prompt):
    top_similar_file_names, top_similar_scores = find_similarities(prompt)
    print(f'Tarefas similares:')
    for index in range(len(top_similar_file_names)):
        file_content = load(f'{TASKS_FILES_PATH}{top_similar_file_names[index]}')
        print(f'Tarefa: {top_similar_file_names[index].split('.')[0]} ({top_similar_scores[index] * 100:.1f}%)')
        print(file_content)

    # system_prompt = f'''
    #     Você é um assistent que usa dados de um helpdesk para recomendar correções para alguns problemas.
    #
    #     Dados o quesitonamento:
    #     {prompt}
    #
    #     E o texto similar
    #     {find_similarities(prompt)}
    #
    #     Verifique se há relação entre esses conteúdos e informa o usuario como ele pode resolver o problema.
    #
    #     # Formado de resposta
    #     - Número da tarefa relacionada, no formato 0000000
    #     - Possivel solução
    # '''
    #
    # response = client.chat.completions.create(
    #     model="gpt-3.5-turbo",
    #     messages=[
    #         {
    #             "role": "system",
    #             "content": system_prompt
    #         }
    #     ]
    # )
    #
    # return response.choices[0].message.content


def adjust_json_file_content():
    cleaned_files_directory = f'{TASKS_FILES_PATH}cleaned/'
    if not os.path.exists(cleaned_files_directory):
        os.makedirs(cleaned_files_directory)
    for filename in os.listdir(TASKS_FILES_PATH):
        if filename.endswith('.txt'):
            file_path = os.path.join(TASKS_FILES_PATH, filename)
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
            filtered_lines = [line for line in lines if '```json' not in line and '```' not in line]
            json_content = ''.join(filtered_lines)
            new_file_path = os.path.join(cleaned_files_directory, filename)
            with open(new_file_path, 'w', encoding='utf-8') as new_file:
                new_file.write(json_content)


def find_similarities_task(task_id):
    task_content = get_task_content(task_id)
    print(f'Conteúdo da tarefa: {task_id}\n{task_content}')
    generate_recomendation(task_content)


def find_similarities_task_problem_only(task_id):
    task_content = get_task_content(task_id)
    problem = extract_title_and_problem_from_task_text(task_content)
    print(f'Conteúdo da tarefa: {task_id}\n{task_content}')
    print(f'Problema da tarefa: {task_id}\n{problem}')
    generate_recomendation(problem)


def generata_embeddings():
    tasks_to_embbed = []
    content = load('data/tasks_to_embbed.txt')
    separators = ',|;|\n'
    for task in re.split(separators, content):
        tasks_to_embbed.append(int(task))
    generate_embeddings(tasks_to_embbed)

# print(generate_recomendation('problema ao confirmar rematricula'))
# print(find_similarities_task(1080961))
# print(find_similarities_task_problem_only(1079781))

# print(get_task_content(1008757))
# generate_embeddings_problem_only()
# adjust_json_file_content()
# generate_embeddings()
