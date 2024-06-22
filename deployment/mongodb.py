import json
import uuid
from pymongo import MongoClient

with open('config.json', 'r') as f:
    config = json.load(f)

client = MongoClient('0.0.0.0', 27017, username=config['username'], password=config['password']).table_llm

def insert_chat(question, answer, file_detail):
    session_id = str(uuid.uuid1())
    client.chat.insert_one({
        'session_id': session_id,
        'question': question,
        'answer': answer,
        'file_detail': file_detail,
        'vote': 0
    })
    return session_id

def update_vote_by_session_id(vote, session_id):
    res = client.chat.update_one(
        {'session_id': session_id},
        {'$set': {'vote': vote}}
    )
    return res

def get_random_wtq():
    res = list(client.wtq.aggregate([{ '$sample': { 'size': 1 } }]))[0]
    return res

def get_random_table_op():
    res = list(client.table_op.aggregate([{ '$sample': { 'size': 1 } }]))[0]
    return res

def get_random_table_merge():
    res = list(client.table_merge.aggregate([{ '$sample': { 'size': 1 } }]))[0]
    return res
