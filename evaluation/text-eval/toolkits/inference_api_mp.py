import concurrent.futures
import json
from tqdm import tqdm
from openai import OpenAI
import re

base_prompt = "[Instruction]\nPlease act as an impartial judge and evaluate the quality of the response provided by an AI assistant to the user question displayed below. Your evaluation should consider factors such as the helpfulness, relevance, accuracy, depth, creativity, and level of detail of the response. Begin your evaluation by providing a short explanation. You will be given a high-quality reference answer and the assistant's answer. Be as objective as possible. You should first provide your explanation IN CHINESE, then you must rate the response on a scale of 1 to 10 by STRICTLY following the below MAPPING for the relation between the scores and response quality:\n1) The score 1~2 stands for very chaotic or absence of answer, and the AI assissant completely failed to address the instructions. The gap between the AI assistant's answer and the high-quality reference answer is huge and insuperable.\n2) The score 3~4 indicates fragment-like responses from AI assistant's answer. It did not provide answers in proper grammar, fluency, or accuracy. There are obvious gaps between the high-quality reference answer and the AI assistant's response.\n3) The score 5~6 indicates for existence of minute disadvantage from the AI assistant's answer compared to the high-quality reference answer. Yet the AI assistant did provide an average answer. The AI assistant either did not fully satisfy instructions, or was somewhat short of helpfulness, relevance, depth, creativity, or detailedness. The disadvantages from the AI assistant's answer overwhelm its advantages.\n4) The score 7~8 indicates the AI assistant provided a good answer as well as the high-quality reference answer, satisfying the instruction, while addressing good helpfulness, relevance, accuracy, depth, creativity, and level of detail of the response. The AI assistant might have flaws compared to the reference answer, but that does not overwhelm the above advantages.\n5) The score 9~10 indicates the AI assistant responsed better than the provided reference answer in most aspects, fully achieved the instruction goal, and have unique advantages to the reference answer.\nYou should give scores around 7 if you do not find obvious advantages or disadvantages. You should seriously consider the above guide before give lowest and highest scores such as 1 or 10, and avoid such situation if you do not have sound explanations.\nAvoid any positional biases and ensure that the order in which the responses were presented does not influence your decision. Do not allow the length of the responses to influence your evaluation. Do not favor certain names of the assistants. AND again, VERY IMPORTANTLY, after you provide your explanation IN CHINESE, you must rate the response strictly following this format: \"[[rating]]\", for example: \"Rating: [[5]]\".\n\n[Question]\n{question}\n\n[The Start of Reference Answer]\n{ref_answer}\n[The End of Reference Answer]\n\n[The Start of Assistant's Answer]\n{answer}\n[The End of Assistant's Answer]"


client = OpenAI(
    base_url='https://api.deepseek.com/v1',
    api_key='api_key',
)
model = 'deepseek-chat'

def load_jsonl(filename):
    with open(filename, "r") as f:
        return [json.loads(line) for line in f]


def send_message(messages):
    """ 发送单个 message """
    answers = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": base_prompt.format(question=messages['prompt'], ref_answer=messages['reference_answer'],answer=messages["assistant_answer"])}],
        temperature=0,
        max_tokens=4096,
        top_p=0.95,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None,
    )
    responses = [response.message.content for response in answers.choices if response.finish_reason != 'length']

    pattern = r'\[\[(.*?)\]\]'
    scores = []
    for ii in responses:
        match = re.search(pattern, ii)
        try: 
            score = match.group(1)
            scores.append(int(score))
        except:
            print("not found")
            scores.append(-1)

    return {
        'question': messages['question'],
        'prompt': messages['prompt'],
        'reference_answer': messages['reference_answer'],
        'assistant_answer': messages['assistant_answer'],
        'judgement': responses,
        'scores': scores
    }


def process_chunk(chunk, max_concurrency):
    """ Process a chunk of messages """
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrency) as executor:
        results = list(executor.map(lambda msg: send_message(msg), chunk))
    return results

def append_to_jsonl(results, jsonl_file):
    """ Append the result of the chunk to the jsonl file """
    with open(jsonl_file, 'a+') as f:
        for result in results:
            f.write(json.dumps(result, ensure_ascii=False) + '\n')

def inference_api_mp(messages, chunk_size, max_concurrency, jsonl_file):
    """ Read and process by chunks """
    for i in tqdm(range(0, len(messages), chunk_size)):

        chunk = messages[i:i + chunk_size]
        
        chunk_results = process_chunk(chunk, max_concurrency)

        append_to_jsonl(chunk_results, jsonl_file)

