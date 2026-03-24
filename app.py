from flask import Flask, send_file
import os

app = Flask(__name__)

@app.route('/<filename>')
def serve(filename):
    if os.path.exists(filename):
        return send_file(filename)
    return "File not found", 404

@app.route('/')
def home():
    return "Bot is running!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)