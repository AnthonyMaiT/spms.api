# See Credits in README.md 
import random
import json

import torch

from .model import NeuralNet
from .nltk_utils import bag_of_words, tokenize

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

with open('./chatbot/intents/student_intents.json', 'r') as json_data:
    student_intents = json.load(json_data)
with open('./chatbot/intents/staff_intents.json', 'r') as json_data:
    staff_intents = json.load(json_data)
with open('./chatbot/intents/admin_intents.json', 'r') as json_data:
    admin_intents = json.load(json_data)

STUDENT_FILE = "./chatbot/data/student_data.pth"
STAFF_FILE = "./chatbot/data/staff_data.pth"
ADMIN_FILE = "./chatbot/data/admin_data.pth"

def load_data(file: str):
    data = torch.load(file)

    input_size = data["input_size"]
    hidden_size = data["hidden_size"]
    output_size = data["output_size"]
    all_words = data['all_words']
    tags = data['tags']
    model_state = data["model_state"]

    model = NeuralNet(input_size, hidden_size, output_size).to(device)
    model.load_state_dict(model_state)
    model.eval()
    return [model, all_words, tags]

student = load_data(STUDENT_FILE)
staff = load_data(STAFF_FILE)
admin = load_data(ADMIN_FILE)

def get_response(msg, role_type_id: int):
    user_data_list = []
    if role_type_id == 1:
        user_data_list = admin
    elif role_type_id == 2:
        user_data_list = staff
    elif role_type_id == 3:
        user_data_list = student
    sentence = tokenize(msg)
    X = bag_of_words(sentence, user_data_list[1])
    X = X.reshape(1, X.shape[0])
    X = torch.from_numpy(X).to(device)

    output = user_data_list[0](X)
    _, predicted = torch.max(output, dim=1)

    tag = user_data_list[2][predicted.item()]

    probs = torch.softmax(output, dim=1)
    prob = probs[0][predicted.item()]
    if prob.item() > 0.75:
        if role_type_id == 1:
            for intent in admin_intents['intents']:
                if tag == intent["tag"]:
                    return random.choice(intent['responses'])
        elif role_type_id == 2:
            for intent in staff_intents['intents']:
                if tag == intent["tag"]:
                    return random.choice(intent['responses'])
        elif role_type_id == 3:
            for intent in student_intents['intents']:
                if tag == intent["tag"]:
                    return random.choice(intent['responses'])
    return "I do not understand..."