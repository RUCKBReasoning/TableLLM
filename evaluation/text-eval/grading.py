import json
import gc
import torch
from vllm import LLM, SamplingParams
from vllm.model_executor.parallel_utils.parallel_state import destroy_model_parallel

def get_critique_prompt(question , ref_answer , answer):
    return f'''
[Question]\n{question}\n\n[The Start of Reference Answer]\n{ref_answer}\n[The End of Reference Answer]\n\n[The Start of Assistant's Answer]\n{answer}\n[The End of Assistant's Answer]
'''

def grading(model_name, base_dir):
    # load model
    llm = LLM(model='/workspace/mzy/MODELS/0113_9_swap_no_base',trust_remote_code=True) # critique model ckpt

    file_path = f'{base_dir}/Infer_{model_name}.jsonl'
    # load test data
    with open(file_path , 'r') as fp:
        lines = fp.readlines()
        
    datas = [json.loads(i) for i in lines]
    prompts = []
    for data in datas:
        prompt = data['prompt']
        reference_answer = data['reference_answer']
        assitant_answer = data['assistant_answer']
        data['instruction'] = get_critique_prompt(question=prompt , ref_answer=reference_answer , answer=assitant_answer)
        prompts.append(data['instruction'])


    # get LLM response
    sampling_params = SamplingParams(temperature=0.8, top_p=0.95, max_tokens=768, n = 5)

    responses = llm.generate(prompts, sampling_params=sampling_params)

    # save to file
    output = []
    for i in range(len(lines)):
        data = json.loads(lines[i])
        data['instruction'] = get_critique_prompt(question=data['prompt'], ref_answer=data['reference_answer'] , answer=data['assistant_answer'])
        data['judgement'] = [response.text.strip(' ') for response in responses[i].outputs]
        output.append(json.dumps(data, ensure_ascii=False) + '\n')  
    with open(f'{base_dir}/Grade_{model_name}.jsonl', 'w') as fp:
        fp.writelines(output)
        
    destroy_model_parallel()
    del llm
    gc.collect()
    torch.cuda.empty_cache()
