#!/usr/bin/env python

from flask import Flask, request
from flask import render_template
import atlas

app = Flask(__name__)

@app.route("/")
def home():
    return app.send_static_file('index.html')

@app.route("/respond", methods=['POST'])
def respond():
    bot.speakResponse(request.form['input'])
    return app.send_static_file('index.html')

if __name__ == '__main__':
    bot = atlas.Atlas()
    bot.initialize("aiml")
    app.run(debug=True, host='127.0.0.1', port=3000)