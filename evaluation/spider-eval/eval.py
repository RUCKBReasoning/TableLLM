import warnings
warnings.filterwarnings('ignore')
import re
import os
import sys
import json
import runpy
import argparse
import collections
import numpy as np
import pandas as pd
from tqdm import tqdm
from io import StringIO


def contains_open_with_write_or_append(text):
    pattern1 = r'\bopen\s*\([^)]*\s*[,]\s*[\'"](?:w(?:b)?|a(?:b)?)'
    match1 = re.search(pattern1, text)
    pattern2 = r'\.to_csv\s*\('
    match2 = re.search(pattern2, text)
    return match1 is not None or match2 is not None


def run_code(code):
    try:
        # 临时写入文件
        tmp_path = 'tmp/tmp.py'
        with open(tmp_path, 'w') as fp:
            fp.write(code)

        # 运行文件
        sys.stdout = StringIO()
        variables = runpy.run_path(tmp_path)
        output_str = sys.stdout.getvalue()
        sys.stdout.close()
        sys.stdout = sys.__stdout__  # 恢复stdout

        # 从print中提取参数名
        output_variable_name = re.findall('print\((.*?)\)', code)
        if len(output_variable_name) == 0:
            return None
        output_variable_name = output_variable_name[0]
        while output_variable_name.find(',') != -1:
            output_variable_name = output_variable_name[output_variable_name.find(',') + len(', '):]

        # 找到输出的变量
        output_variable = variables[output_variable_name]

    except Exception as e:
        sys.stdout = sys.__stdout__  # 恢复stdout
        return None
    return output_variable


def is_correct(code_result, ground_result, ground_result_list):
    # get llm_result and llm_result_list
    if isinstance(code_result, pd.DataFrame):
        llm_result_list = []
        for row in code_result.values.tolist():
            llm_result_list.extend(row)
        llm_result = ','.join(','.join(str(e) for e in row) for row in code_result.values.tolist())
    elif isinstance(code_result, pd.Series):
        llm_result_list = code_result.tolist()
        llm_result = ','.join(str(e) for e in code_result.tolist())
        if ground_result != llm_result:
            llm_result_list = []
            for e in code_result.items():
                llm_result_list.append(e[0])
                llm_result_list.append(e[1])
            llm_result = ','.join(f'{str(e[0])},{str(e[1])}' for e in code_result.items())
    elif isinstance(code_result, (np.ndarray, pd.Index)):
        llm_result_list = code_result.tolist()
        llm_result = ','.join(str(e) for e in code_result.tolist())
    elif isinstance(code_result, (list, set, tuple)):
        llm_result_list = [e for e in code_result]
        llm_result = ','.join(str(e) for e in code_result)
    elif isinstance(code_result, dict):
        llm_result_list = [code_result[key] for key in code_result]
        llm_result = ','.join(str(code_result[key]) for key in code_result)
    elif isinstance(code_result, (int, float, np.int64, np.float64, pd.Timestamp, pd.Timedelta)):
        llm_result_list = [str(code_result)]
        llm_result = str(code_result)
    elif isinstance(code_result, str):
        llm_result_list = [code_result]
        llm_result = code_result
    else:
        print(type(code_result))
        llm_result_list = []
        llm_result = ''

    # is correct
    if ground_result == llm_result:
        return True

    # convert int to float and finally to string
    for i in range(len(ground_result_list)):
        if isinstance(ground_result_list[i], int) or \
            (isinstance(ground_result_list[i], str) and ground_result_list[i].isdigit()):
            ground_result_list[i] = float(ground_result_list[i])
        ground_result_list[i] = str(ground_result_list[i])
    for i in range(len(llm_result_list)):
        if isinstance(llm_result_list[i], (int, np.int64)):
            llm_result_list[i] = float(llm_result_list[i])
        llm_result_list[i] = str(llm_result_list[i])

    # determine if 2 lists have the same elements, regardless of order
    if collections.Counter(ground_result_list) == collections.Counter(llm_result_list):
        return True
    
    return False


def eval(args):
    os.makedirs('tmp', exist_ok=True)
    # load data
    with open(args.infer_data, 'r') as fp:
        datasets = [json.loads(line) for line in fp.readlines()]

    correct_num = 0
    error_num = 0
    for data in tqdm(datasets):
        execution_results = data["execution_results"]
        ground_result = ','.join(','.join(str(e) for e in row) for row in execution_results)
        ground_result_list = []
        for row in execution_results:
            ground_result_list.extend(row)

        code = data['assistant_code']
        if contains_open_with_write_or_append(code):
            continue

        if '```python' in code:
            code = code[code.find('```python') + len('```python'):]
            code = code[:code.find('```')]
        elif '```' in code:
            code = code[code.find('```') + len('```'):]
            code = code[:code.find('```')]

        if code.find("import pandas as pd") == -1:
            code = f"import pandas as pd\n\ndf = pd.read_csv('data.csv')\n\n{code}"

        code_result = run_code(code.replace('data.csv', data["table_data_path"]))
        if code_result is None:
            error_num += 1
            continue

        if is_correct(code_result, ground_result, ground_result_list):
            correct_num += 1

    print(f'Accuracy: {round(correct_num * 100 / len(datasets), 2)}%')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--infer_data', required=True, type=str, help='inference data path')
    args = parser.parse_args()

    eval(args)
