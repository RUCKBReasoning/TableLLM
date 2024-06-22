import random
import pandas as pd

from mongodb import get_random_wtq, get_random_table_op, get_random_table_merge


def get_single(last_table=None):
    chat_mode = 'QA' if random.randint(0, 2) == 0 else 'Code'

    if chat_mode == 'QA':
        chosen_data = get_random_wtq()
        if last_table is not None:
            while last_table == chosen_data['table_in_csv']:
                chosen_data = get_random_wtq()
        
        file_name = chosen_data['csv_path']
        local_path = f"default_data/tables/{file_name}"
        table = chosen_data['table_in_csv']
        df = pd.read_csv(local_path)
        file_detail = {
            'name': file_name,
            'local_path': local_path,
            'dfs_path': '',
            'size': '',
            'description': chosen_data['description']
        }
        questions = chosen_data['questions']

    elif chat_mode == 'Code':
        chosen_data = get_random_table_op()

        with open(f'default_data/tables/{chosen_data["csv_path"]}', 'r') as fp:
            table = ''.join(fp.readlines()[:11])

        if last_table is not None:
            while last_table == table:
                chosen_data = get_random_table_op()
                with open(f'default_data/tables/{chosen_data["csv_path"]}', 'r') as fp:
                    table = ''.join(fp.readlines()[:11])

        file_name = chosen_data['csv_path']
        local_path = f'default_data/tables/{file_name}'

        df = pd.read_csv(local_path)
        file_detail = {
            'name': file_name,
            'local_path': local_path,
            'dfs_path': '',
            'size': '',
        }
        questions = chosen_data['questions']
    
    random.shuffle(questions)
    return table, df, file_detail, questions, chat_mode


def get_double():
    chosen_data = get_random_table_merge()

    file_names = [chosen_data["csv1_path"], chosen_data["csv2_path"]]
    local_paths = [
        f'default_data/tables/{chosen_data["csv1_path"]}',
        f'default_data/tables/{chosen_data["csv2_path"]}'
    ]
    questions = chosen_data['questions']
    tables, dfs, file_details = [], [], []
    for i in range(2):
        with open(local_paths[i], 'r') as fp:
            table = ''.join(fp.readlines()[:11])
        tables.append(table)
        dfs.append(pd.read_csv(local_paths[i]))
        file_details.append({
            'name': file_names[i],
            'local_path': local_paths[i],
            'dfs_path': '',
            'size': '',
        })

    return tables, dfs, file_details, questions
