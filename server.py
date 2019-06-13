#!/usr/bin/env python

from flask import Flask, flash, request, url_for
from flask import render_template
import atlas
import time
app = Flask(__name__)

app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'


history = dict()

@app.route("/", methods=['POST', 'GET'])
def messenger():
    global history
    response = ""
    if request.method == 'POST':
        if request.form['button'] == 'Submit':
            response = bot.respond(
                request.form['question'])
            history[request.form['question']] = response

        if request.form['button'] == 'Clear':
            history = dict()
    return render_template("messenger.html", history=history)


@app.route("/speech-recognition")
def speechrecognition():
    return app.send_static_file('index.html')
@app.route("/hey-atlas")
def heyatlas():
    return app.send_static_file('user-media.html')

@app.route("/respond", methods=['POST'])
def respond():
    return bot.respond(request.form['input'])


if __name__ == '__main__':
    bot = atlas.Atlas()
    bot.initialize("aiml")
    history = dict()
    app.run(debug=True, host='127.0.0.1', port=3000)
