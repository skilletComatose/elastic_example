import json
import time
import random
import os

def generate_json_data(age):
    return json.dumps({"age": age, "other": random.randint(0,9) })


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