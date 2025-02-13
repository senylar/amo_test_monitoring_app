from flask import Flask, jsonify
import random
import time

app = Flask(__name__)

def gen():
    return 70


@app.route('/stub/server/<int:server_id>')
def metrics(server_id):
    return jsonify({"cpu": random.randint(90, 100), "mem": f"{random.randint(0, 10)}%", "disk": f"{random.randint(0, 100)}%",
         "uptime": f"{random.randint(1, 30)}d {random.randint(0, 23)}h {random.randint(0, 59)}m",'cpu':95,'mem':'93%','disk':'85%'})

if __name__ == '__main__':
    app.run(port=5000)