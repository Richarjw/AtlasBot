#!/usr/bin/env python

import aiml
import os
import sys
import subprocess


class Atlas():
    def __init__(self):
        self._kernel = aiml.Kernel()
        self.messages = []
        self.responses = []

    def initialize(self, aiml_dir):
        self._kernel.learn(os.sep.join([aiml_dir, '*.aiml']))
        self.messages = []
        self.responses = []
        properties_file = open(os.sep.join([aiml_dir, 'bot.properties']))
        for line in properties_file:
            parts = line.split('=')
            key = parts[0]
            value = parts[1]
            self._kernel.setBotPredicate(key, value)

    def respond(self, input):
        response = self._kernel.respond(input)
        return response

    def speak(self, response):
        return response

    def speakResponse(self, input):
        str = self.speak(self.respond(input))
        self.messages.append(input)
        self.responses.append(str)
        return str

def main():
    atlas = Atlas()
    atlas.initialize("aiml")  # parameter is the aiml directory

    while True:
        n = input("Input: ")
        atlas.speakResponse(n)


if __name__ == '__main__':
    main()
