import re
import sys
import json
import runpy
import argparse
import warnings
warnings.filterwarnings('ignore')
import pandas as pd
from tqdm import tqdm
from io import StringIO
from critique_llm import infer_critique_grade


def get_judgement_score(input_str):
    pattern = r'\[\[(.*?)\]\]'
    matches = re.findall(pattern, input_str)
    return matches[0]


def contains_open_with_write_or_append(text):
    pattern1 = r'\bopen\s*\([^)]*\s*[,]\s*[\'"](?:w(?:b)?|a(?:b)?)'
    match1 = re.search(pattern1, text)
    pattern2 = r'\.to_csv\s*\('
    match2 = re.search(pattern2, text)
    return match1 is not None or match2 is not None


def run_code(code, instruction_type):
    if contains_open_with_write_or_append(code):
        return None
    try:
        # write file
        if instruction_type == 'Draw':
            code = code.replace('plt.show()', '')
            return ''
        code = code.replace('infiagent', '/workspace/mzy/home_mzy/TLLM/table-op-eval/infiagent')
        code = code.lstrip('\n').lstrip(' ')
        tmp_path = '/workspace/mzy/home_mzy/TLLM/table-op-eval/tmp/tmp.py'
        with open(tmp_path, 'w') as fp:
            fp.write(code)
        
        # run file, get the variables and console output
        sys.stdout = StringIO()
        # exec(code)
        # variables = locals()
        variables = runpy.run_path(tmp_path)
        output_str = sys.stdout.getvalue().rstrip('\n')
        sys.stdout.close()
        sys.stdout = sys.__stdout__  # resume stdout

        # no error occur
        if instruction_type == 'Draw':
            answer = ''
        elif instruction_type == 'Query':
            answer = output_str
            if len(answer) > 2000:
                answer = answer[:2000]
        else:  # Insert/Delete/Update/Merge
            # extract variable name from print()
            output_variable_name = re.findall('print\((.*?)\)', code)
            if len(output_variable_name) == 0:
                return None
            output_variable_name = output_variable_name[0]
            while output_variable_name.find(',') != -1:
                output_variable_name = output_variable_name[output_variable_name.find(',') + len(', '):]

            # find the output variable
            output_variable = variables[output_variable_name]
            answer = output_variable

        return answer
    except Exception as e:
        sys.stdout = sys.__stdout__  # resume stdout
        return None


def get_code_answer(datasets):
    for i in tqdm(range(len(datasets))):
        instruction_type = datasets[i]['instruction_type'][:datasets[i]['instruction_type'].find('-')]
        datasets[i]['reference_answer'] = run_code(datasets[i]['reference_code'], instruction_type)
        if instruction_type == 'Merge':
            assistant_code = datasets[i]['assistant_code'].replace('data1.csv', datasets[i]['csv1_path'])
            assistant_code = assistant_code.replace('data2.csv', datasets[i]['csv2_path'])
        else:
            assistant_code = datasets[i]['assistant_code'].replace('data.csv', datasets[i]['csv_path'])
        datasets[i]['assistant_answer'] = run_code(assistant_code, instruction_type)
        datasets[i]['is_error'] = 'yes' if datasets[i]['assistant_answer'] is None else 'no'


def grading(args):
    # load data
    with open(args.infer_data, 'r') as fp:
        datasets = [json.loads(line) for line in fp.readlines()]
    
    # run code
    get_code_answer(datasets)

    # run critique llm
    infer_critique_grade(datasets)

    # evaluate
    pass_num = 0
    for data in datasets:
        instruction_type = data['instruction_type'][:data['instruction_type'].find('-')]
        if data['is_error'] == 'yes':
            data['is_pass'] = 'no'
        elif instruction_type == 'Draw':
            try:
                judgement_score = int(get_judgement_score(data['judgement']))
                data['is_pass'] = 'yes' if judgement_score >= 5 else 'no'
            except:
                print(data['judgement'])
                data['is_pass'] = 'no'
        elif instruction_type == 'Insert' or instruction_type == 'Query':
            if type(data['reference_answer']) == type(data['assistant_answer']) and \
                data['reference_answer'].equals(data['assistant_answer']):
                data['is_pass'] = 'yes'
            else:
                # only compare values to avoid the difference of newly insert column name
                if not isinstance(data['assistant_answer'], pd.DataFrame):
                    data['is_pass'] = 'no'
                else:
                    try:
                        reference_answer = '\n'.join(','.join(str(e) for e in row.tolist()) for _, row in data['reference_answer'].iterrows())
                        assistant_answer = '\n'.join(','.join(str(e) for e in row.tolist()) for _, row in data['assistant_answer'].iterrows())
                        data['is_pass'] = 'yes' if reference_answer == assistant_answer else 'no'
                    except:
                        data['is_pass'] = 'no'
        else:
            if type(data['reference_answer']) == type(data['assistant_answer']) and \
                data['reference_answer'].equals(data['assistant_answer']):
                data['is_pass'] = 'yes'
            else:
                data['is_pass'] = 'no'
        pass_num += 1 if data['is_pass'] == 'yes' else 0

    # save result
    output = []
    for data in datasets:
        data.pop('reference_answer')
        data.pop('assistant_answer')
        output.append(json.dumps(data, ensure_ascii=False) + '\n')
    model_name = args.infer_data[args.infer_data.rfind('/') + 1:] if args.infer_data.find('/') != -1 else args.model_path
    with open(f'../../inference/results/Grade_{model_name}.jsonl', 'w') as fp:
        fp.writelines(output)

    print(f'The grade of {model_name} is:')
    print(f'Pass number: {pass_num}')
    print(f'Fail number: {len(datasets) - pass_num}')
    print(f'Accuracy: {round(100 * pass_num / len(datasets), 2)}%')


def get_grade(model_name, base_dir):
    with open(f'{base_dir}/Grade_{model_name}.jsonl', 'r') as fp:
        datasets = [json.loads(line) for line in fp.readlines()]
    
    pass_num = 0
    for data in datasets:
        pass_num += 1 if data['is_pass'] == 'yes' else 0

    print(f'The grade of {model_name} is:')
    print(f'Pass number: {pass_num}')
    print(f'Fail number: {len(datasets) - pass_num}')
    print(f'Accuracy: {round(100 * pass_num / len(datasets), 2)}%')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--infer_data', required=True, type=str, help='inference data path')
    args = parser.parse_args()
    
    grading(args.infer_data)
