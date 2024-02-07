import warnings
warnings.filterwarnings('ignore')
import re
import csv
import sys
import json
import runpy
import argparse
import numpy as np
import pandas as pd
from tqdm import tqdm
from io import StringIO


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


def _split_thousands(delimiter, value):
    split = value.split(delimiter)
    return len(split) > 1 and any((len(x) == 3 for x in split))


def to_date(value):
    year = value.year
    month = value.month_name()
    day = value.day
    return f'{month} {day}, {year}'


def convert_to_float(value):
    """Converts value to a float using a series of increasingly complex heuristics.
    Args:
      value: object that needs to be converted. Allowed types include
        float/int/strings.
    Returns:
      A float interpretation of value.
    Raises:
      ValueError if the float conversion of value fails.
    """
    if isinstance(value, float):
        return value
    if isinstance(value, (int, np.int64)):
        return float(value)
    if isinstance(value, np.bool_):
        return '1' if value else '0'
    if isinstance(value, np.datetime64):
        pd_datetime = pd.to_datetime(value)
        return to_date(pd_datetime)
    if isinstance(value, pd.Timestamp):
        return to_date(value)
    if isinstance(value, pd.Timedelta):
        return str(value)
    if isinstance(value, (list, tuple, set)):
        return ', '.join(str(e) for e in value)
    if isinstance(value, dict):
        return ', '.join(str(v) for _, v in value.items())
    if not isinstance(value, str):
        print(type(value))
        return ''
    sanitized = value

    try:
        # Example: 1,000.7
        if "." in sanitized and "," in sanitized:
            return float(sanitized.replace(",", ""))
        # 1,000
        if "," in sanitized and _split_thousands(",", sanitized):
            return float(sanitized.replace(",", ""))
        # 5,5556
        if "," in sanitized and sanitized.count(",") == 1 and not _split_thousands(",", sanitized):
            return float(sanitized.replace(",", "."))
        # 0.0.0.1
        if sanitized.count(".") > 1:
            return float(sanitized.replace(".", ""))
        # 0,0,0,1
        if sanitized.count(",") > 1:
            return float(sanitized.replace(",", ""))
        return float(sanitized)
    except ValueError:
        return sanitized


def check_none(value):
    if value is None or isinstance(value, type(pd.NaT)):
        return True


def eval(args):
    with open(args.infer_data, 'r') as fp:
        infer_data = [json.loads(line) for line in fp.readlines()]

    correct = 0
    all_num = 0
    error_num = 0
    for data in tqdm(infer_data):
        ground_result = ', '.join(data['ref_answer_list'])
        all_num += 1

        # save csv file
        with open('tmp/tmp.csv', 'w') as fp:
            csv_writer = csv.writer(fp)
            csv_writer.writerows(data['table'])

        # run code
        code = data['assistant_code']
        if code.find("import pandas as pd") == -1:
            code = f"import pandas as pd\n\ndf = pd.read_csv('data.csv')\n\n{code}"
        code = code.replace('data.csv', 'tmp/tmp.csv')
        llm_result_org = run_code(code)

        # re-format result to list
        if isinstance(llm_result_org, (pd.Series, np.ndarray)):
            llm_result_org = llm_result_org.tolist()
        elif isinstance(llm_result_org, pd.DataFrame):
            llm_result_org = llm_result_org.values.tolist()
        elif not isinstance(llm_result_org, list):
            llm_result_org = [llm_result_org]
        
        # for each element in the list
        for j in range(len(llm_result_org)):
            if check_none(llm_result_org[j]):
                llm_result_org[j] = 'none'
            else:
                llm_result_org[j] = convert_to_float(llm_result_org[j])
        llm_result = ', '.join([str(e) for e in llm_result_org])
        if llm_result == 'none' and ground_result != 'none':
            error_num += 1

        if ground_result == 'none':
            all_num -= 1
            continue
        if llm_result == ground_result:
            correct += 1

    print(f'Accuracy: {round(100 * correct / all_num, 2)}%')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--infer_data', required=True, type=str, help='inference data path')
    args = parser.parse_args()

    eval(args)
