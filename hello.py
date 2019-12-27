import json
import os

from flask import Flask, escape, request

app = Flask(__name__)

@app.route('/')
def hello():
    name = request.args.get("name", "World")
    env = str(os.environ)
    return f'Hello, {escape(name)}! -- {env}'


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
