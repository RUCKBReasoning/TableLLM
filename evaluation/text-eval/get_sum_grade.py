import re
import json
import argparse
from grading import grading


def find_content_between_double_square_brackets(input_str):
    pattern = r'\[\[(.*?)\]\]'
    matches = re.findall(pattern, input_str)
    return matches[0]


def y_or_n(input_str, threshold):
    try:
        jud = int(find_content_between_double_square_brackets(input_str))
    except:
        jud = 0
    if jud >= threshold:
        return 1
    else:
        return 0


def get_result(args):
    thresholds = 7
    results = 0

    with open(args.grade_data, 'r', encoding='utf-8') as fp:
        datasets = [json.loads(line) for line in fp.readlines()]

    for data in datasets:
        flag = 0
        for item in data['judgement']:
            flag += y_or_n(item, thresholds)
        if flag >= 3:  
            results += 1
                
    print(f'Accuracy: {round(100 * results / len(datasets), 2)}%')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--grade_data', required=True, type=str, help='inference data path')
    args = parser.parse_args()
    grading(args)
    get_result(args)
