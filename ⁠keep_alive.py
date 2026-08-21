from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot is active!"

def keep_alive():
    t = Thread(target=lambda: app.run(host='0.0.0.0', port=10000))
    t.start()
