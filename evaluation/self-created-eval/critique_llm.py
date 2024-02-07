from vllm import LLM, SamplingParams


PROMPT_FORMAT = '''[Question]
{question}

[The Start of Reference Answer]
{ref_answer}
[The End of Reference Answer]

[The Start of Assistant's Answer]
{answer}
[The End of Assistant's Answer]'''


def infer_critique_grade(datasets):
    # load data
    prompts = []
    for data in datasets:
        instruction_type = data['instruction_type'][:data['instruction_type'].find('-')]
        if instruction_type == 'Draw':
            question = data['prompt']
            prompt = PROMPT_FORMAT.format_map({
                'question': question,
                'ref_answer': data['reference_code'],
                'answer': data['assistant_code']
            })
            prompts.append(prompt)

    # load model
    llm = LLM(model='model_path', trust_remote_code=True)

    # get response
    sampling_params = SamplingParams(temperature=0.8, top_p=0.95, max_tokens=768)
    responses = llm.generate(prompts, sampling_params=sampling_params)

    # save result
    response_index = 0
    for i in range(len(datasets)):
        instruction_type = datasets[i]['instruction_type'][:datasets[i]['instruction_type'].find('-')]
        if instruction_type == 'Query' or instruction_type == 'Draw':
            datasets[i]['judgement'] = responses[response_index].outputs[0].text.lstrip(' ')
            response_index += 1
        else:
            datasets[i]['judgement'] = ''
