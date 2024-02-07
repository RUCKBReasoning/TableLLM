import json
import argparse
from vllm import LLM, SamplingParams


def inference(args):
    # load test data
    with open(f'../benchmark/{args.dataset}.jsonl', 'r') as fp:
        datasets = [json.loads(line) for line in fp.readlines()]
    prompts = [f"[INST]{data['prompt']}[/INST]" for data in datasets]

    # load model
    llm = LLM(model=args.model_path, tensor_parallel_size=args.tensor_parallel_size, max_model_len=2048)

    # get LLM response
    sampling_params = SamplingParams(temperature=args.temperature, top_p=args.top_p, max_tokens=512)
    responses = llm.generate(prompts, sampling_params=sampling_params)

    # save to file
    output = []
    for i in range(len(datasets)):
        output.append(json.dumps({
            'question' : datasets[i]['question'],
            'prompt': datasets[i]['prompt'],
            'reference_answer': datasets[i]['answer'],
            'assistant_answer': responses[i].outputs[0].text.lstrip(' ')
        }, ensure_ascii=False) + '\n')
    model_name = args.model_path[args.model_path.rfind('/') + 1:] if args.model_path.find('/') != -1 else args.model_path
    with open(f'results/Infer_{model_name}.jsonl', 'w') as fp:
        fp.writelines(output)

    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', required=True, type=str, help='dataset name')
    parser.add_argument('--model_path', required=True, type=str, help='model path')
    parser.add_argument('--temperature', default=0.8, type=float, help='inference temperature')
    parser.add_argument('--top_p', default=0.95, type=float, help='inference top_p')
    parser.add_argument('--tensor_parallel_size', default=1, type=int, help='gpu numbers')
    args = parser.parse_args()

    inference(args)
