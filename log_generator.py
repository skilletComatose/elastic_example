import json
import time
import random
import os
from faker import Faker
def generate_json_data(age):
    fake = Faker()
    return json.dumps({"name": fake.name(), "age": age })


target:str = "./TODO1/output.json"
os.remove(target)
age = 1
interval = 5
while True:
    json_data = generate_json_data(age)
    with open(target,  "a") as file:
        file.write(json_data + "\n")  
    print(json_data)
    age += 1
    time.sleep(interval)