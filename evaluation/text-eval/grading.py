import json
import argparse
import os
from toolkits.wtq_eval import wtq_eval
from toolkits.tatqa_eval import tatqa_eval
from toolkits.fetaqa_eval import fetaqa_eval

def eval(grade_data):
    if 'wtq' in grade_data:
        wtq_eval(grade_data)
    elif 'tatqa' in grade_data:
        tatqa_eval(grade_data)
    elif 'fetaqa' in grade_data:
        fetaqa_eval(grade_data)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--grade_data', required=False, type=str, help='grade data')
    args = parser.parse_args()
 
    eval(args.grade_data)
