import re
import json
import os
from tqdm import tqdm
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
from toolkits.utils import normalize_answer, exact_match
from rouge_score import rouge_scorer

    
def tatqa_eval(input_file, output_file):
    # load test data
    with open(input_file , 'r', encoding='utf-8') as fp:
        lines = fp.readlines()  
    datas = [json.loads(i) for i in lines]
    
    cnt = 0
    datas_2 = []
    for data in tqdm(datas):
        reference_answer = data['reference_answer']
        assistant_answer = data['assistant_answer']

        if type(reference_answer) != list:
            reference_answer = [str(reference_answer)]

        reference_answer = [normalize_answer(i) for i in reference_answer]
        assistant_answer = normalize_answer(assistant_answer)

        score = 0
        if len(reference_answer) == 1 and len(reference_answer[0]) >= 40: # long sentence
            # rouge-score
            scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)
            rouge_recall = scorer.score(reference_answer[0], assistant_answer)['rougeL'].recall
            score = rouge_recall
        else: # exact match
            is_match = exact_match(reference_answer, assistant_answer.split('therefore')[-1])
            score = 1 if is_match else 0

        data['score'] = score
        datas_2.append(data)

        if score > 0.7:
            cnt += 1
            
    percentage = (cnt / len(datas)) * 100

    formatted_percentage = "{:.2f}%".format(percentage)
    print(f"{input_file.split('/')[-2]}/{input_file.split('/')[-1]}:")
    print(f"percentage: {formatted_percentage}")


    with open(output_file, 'w', encoding='utf-8') as fp:
        for data in datas_2:
            fp.write(json.dumps(data, ensure_ascii=False) + '\n')



    