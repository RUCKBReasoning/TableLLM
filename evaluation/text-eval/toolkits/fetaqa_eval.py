import re
import json
import os
from tqdm import tqdm
from toolkits.inference_api_mp import inference_api_mp

def fetaqa_eval(input_file, output_file):
    # load test data
    with open(input_file , 'r', encoding='utf-8') as fp:
        lines = fp.readlines()
    datas = [json.loads(i) for i in lines]    

    inference_api_mp(datas, 50, 10, output_file)

    with open(output_file, "r") as f:
        grade_datas = [json.loads(line) for line in f]

    cnt = 0
    for item in grade_datas:
        score = item['scores'][0]
        if score >= 7:
            cnt += 1
    
    percentage = (cnt / len(grade_datas)) * 100

    formatted_percentage = "{:.2f}%".format(percentage)
    print(f"{input_file.split('/')[-2]}/{input_file.split('/')[-1]}:")
    print(f"percentage: {formatted_percentage}")
