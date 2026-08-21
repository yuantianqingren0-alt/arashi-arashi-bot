from flask import Flask
from threading import Thread
import os

app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def keep_alive():
    # Renderが指定するPORT環境変数を取得（デフォルトは10000）
    port = int(os.environ.get("PORT", 10000))
    t = Thread(target=lambda: app.run(host='0.0.0.0', port=port))
    t.start()
