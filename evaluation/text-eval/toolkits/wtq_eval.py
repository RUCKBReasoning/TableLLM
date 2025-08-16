import re
import json
from tqdm import tqdm
from toolkits.utils import normalize_answer, exact_match


def wtq_eval(input_file, output_file):

    # load test data
    with open(input_file , 'r', encoding='utf-8') as fp:
        lines = fp.readlines()
        
    datas = [json.loads(i) for i in lines]
    
    datas_2 = []
    cnt = 0
    for data in tqdm(datas):
        reference_answer = [normalize_answer(ref_data) for ref_data in data['reference_answer']]
        assistant_answer = normalize_answer(data['assistant_answer'].split('Therefore,')[-1])

        data['flag'] = exact_match(reference_answer, assistant_answer)
        if data['flag']:
            cnt += 1
        datas_2.append(data)
    
    percentage = (cnt / len(datas)) * 100

    formatted_percentage = "{:.2f}%".format(percentage)
    print(f"{input_file.split('/')[-2]}/{input_file.split('/')[-1]}:")
    print(f"percentage: {formatted_percentage}")

    with open(output_file, 'w', encoding='utf-8') as fp:
        for data in datas_2:
            fp.write(json.dumps(data, ensure_ascii=False) + '\n')

