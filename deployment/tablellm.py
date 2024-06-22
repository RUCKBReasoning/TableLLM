import json
import requests
from transformers import AutoTokenizer

from code_exec import check_code
from mongodb import insert_chat
from prompt_format import QA_PROMPT, CODE_PROMPT, CODE_MERGE_PROMPT, LLAMA2_PROMPT

with open('config.json', 'r') as f:
    config = json.load(f)
URL = config['model_url']
MODEL_PATH = config['model_path']

def get_qa_prompt(question, table, description):
    prompt = QA_PROMPT.format_map({
        'table_descriptions': description,
        'table_in_csv': table,
        'question': question
    })
    return prompt

def get_code_prompt(question, table):
    # load tokenizer
    llama_tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    
    # fit the table length
    table = table.split('\n')
    head = table[0]
    body = table[1:10]
    while len(body) != 0:
        body_str = "\n".join(body)
        prompt = CODE_PROMPT.format_map({
            'csv_data': f'{head}\n{body_str}',
            'question': question
        })
        prompt_len = len(llama_tokenizer(prompt)['input_ids'])
        if prompt_len >= 1536:
            body.pop()
        else:
            break

    return prompt

def get_code_merge_prompt(question, table):
    # load tokenizer
    llama_tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)

    # fit the table length
    table1 = table[0].split('\n')
    head1, body1 = table1[0], table1[1:10]
    table2 = table[1].split('\n')
    head2, body2 = table2[0], table2[1:10]
    while len(body1) != 0:
        body1_str = "\n".join(body1)
        body2_str = "\n".join(body2)
        prompt = CODE_MERGE_PROMPT.format_map({
            'csv_data1': f'{head1}\n{body1_str}',
            'csv_data2': f'{head2}\n{body2_str}',
            'question': question
        })
        prompt_len = len(llama_tokenizer(prompt)['input_ids'])
        if prompt_len >= 1536:
            body1.pop()
            body2.pop()
        else:
            break
    
    return prompt

def get_tablellm_response(question, table, file_detail, mode):

    # get prompt
    if mode == 'QA':
        prompt = get_qa_prompt(question, table, file_detail['description'])
    elif mode == 'Code':
        prompt = get_code_prompt(question, table)
    elif mode == 'Code_Merge':
        prompt = get_code_merge_prompt(question, table)
    prompt = LLAMA2_PROMPT.format_map({'prompt': prompt})
    
    # get TLLM response
    data = {
        'prompt': prompt,
        'stream': False,
        'temperature': 0.8,
        'top_p': 0.95,
        'max_tokens': 512,
        'n': 1 if mode == 'QA' else 2
    }
    res = requests.post(url=URL, json=data)
    if res.status_code == 200:
        res = res.json()['text']
        # select the code which run successfully
        for i in range(data['n']):
            response = res[i][len(prompt):].lstrip(' ')
            if mode != 'QA':
                local_path = file_detail['local_path'] if mode == 'Code' else [file_detail[0]['local_path'], file_detail[1]['local_path']]
                if check_code(code=response, local_path=local_path, is_merge=(mode == 'Code_Merge')):
                    break
    else:
        response = 'Error occur when TLLM genereate response.'
        print(response)

    # save log
    session_id = insert_chat(question=question, answer=response, file_detail=file_detail)
    
    return response, session_id

def get_tllm_response_pure(question, table, table_detail, mode):

    # get prompt
    if mode == 'QA':
        prompt = get_qa_prompt(question, table, table_detail)
    elif mode == 'Code':
        prompt = get_code_prompt(question, table)
    elif mode == 'Code_Merge':
        prompt = get_code_merge_prompt(question, table)
    prompt = LLAMA2_PROMPT.format_map({'prompt': prompt})
    
    # get TLLM response
    data = {
        'prompt': prompt,
        'stream': False,
        'temperature': 0.8,
        'top_p': 0.95,
        'max_tokens': 512,
    }
    res = requests.post(url=URL, json=data)
    return res
