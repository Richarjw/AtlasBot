#!/usr/bin/env python

import aiml
import os
import sys
import subprocess
import re
from io import BytesIO
import pygame
from google.cloud import texttospeech
from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types
import pyaudio
from six.moves import queue
import spacy
import moviebloc
nlp = spacy.load("en_core_web_sm")
AIML_LOC = "aiml"


class Voice(object):
    def __init__(self):
        self.client = texttospeech.TextToSpeechClient()
        self.voice = texttospeech.types.VoiceSelectionParams(
            language_code="en-GB",
            ssml_gender=texttospeech.enums.SsmlVoiceGender.MALE)
        self.audio_config = texttospeech.types.AudioConfig(
            audio_encoding=texttospeech.enums.AudioEncoding.MP3)

    def respond(self, response):
        synthesis = self.synthesizeResponse(response)
        response = self.buildVoice(synthesis)
        self.speak(response)

    def synthesizeResponse(self, text):
        return texttospeech.types.SynthesisInput(text=text)

    def buildVoice(self, synthesis):
        return self.client.synthesize_speech(
            synthesis, self.voice, self.audio_config)

    def speak(self, response):
        pygame.mixer.init()
        buffer = BytesIO(response.audio_content)
        pygame.mixer.music.load(buffer)
        pygame.mixer.music.play()
        return


class Brain(object):
    def __init__(self, voice, aiml_dir):
        self._voice = voice
        self._kernel = aiml.Kernel()
        self._kernel.learn(os.sep.join([aiml_dir, '*.aiml']))
        properties_file = open(os.sep.join([aiml_dir, 'bot.properties']))
        for line in properties_file:
            parts = line.split('=')
            key = parts[0]
            value = parts[1]
            self._kernel.setBotPredicate(key, value)
        self.bloc = False

        self.state_manager = moviebloc.StateManager()

    def analyze_text(self, text):
        doc = nlp(text)
        print("Noun phrases:", [chunk.text for chunk in doc.noun_chunks])
        print(
            "Verbs:", [token.lemma_ for token in doc if token.pos_ == "VERB"])
   
    def receive(self, input):
        if "thanks atlas" in input or "nevermind" in input:
            self.bloc = False
        if "nevermind" in input or "cancel" in input or "stop" in input:
            self.bloc = False
            textResponse = self._kernel.respond(input)
            self.send_to_voice(textResponse)
        if "movie" in input or "movies" in input or "showing" in input:
            self.bloc = True
            response = self.state_manager.action(input)
            self.send_to_voice(response)
        elif self.bloc:
            response = self.state_manager.action(input)
            self.send_to_voice(response)
        else:
            textResponse = self._kernel.respond(input)
            self.send_to_voice(textResponse)
    def send_to_voice(self, response):
        print("Atlas: ", response)
        self._voice.respond(response)


class Ears(object):
    def __init__(self, brain):
        self._brain = brain
        self._rate = 16000
        self._chunk = int(self._rate / 10)
        self._buff = queue.Queue()
        self.closed = True
        self.language_code = 'en-US'  # a BCP-47 language tag
        self.client = speech.SpeechClient()
        self.config = types.RecognitionConfig(
            encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=self._rate,
            language_code='en-US')
        self.streaming_config = types.StreamingRecognitionConfig(
            config=self.config,
            interim_results=True)

    def listen_print_loop(self, responses):
        for response in responses:
            if not response.results:
                continue
            result = response.results[0]
            if not result.alternatives:
                continue
            transcript = result.alternatives[0].transcript
            if result.is_final:
                if re.search(r'\b(exit|quit)\b', transcript, re.I):
                    print('Exiting..')
                    break
                else:
                    self.send_to_brain(transcript)

    def send_to_brain(self, input):
        print("User: ", input)
        self._brain.receive(input)

    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            channels=1, rate=self._rate,
            input=True, frames_per_buffer=self._chunk,
            stream_callback=self._fill_buffer,
        )
        self.closed = False
        return self

    def __exit__(self, type, value, traceback):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        """Continuously collect data from the audio stream, into the buffer."""
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        while not self.closed:
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]
            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break

            yield b''.join(data)


class Atlas():
    def __init__(self):
        self.voice = Voice()
        self.brain = Brain(self.voice, AIML_LOC)
        self.ears = Ears(self.brain)

    def listen(self):
        with self.ears as stream:
            audio_generator = stream.generator()
            requests = (types.StreamingRecognizeRequest(audio_content=content)
                        for content in audio_generator)
            responses = stream.client.streaming_recognize(
                stream.streaming_config, requests)
            print(responses)
            stream.listen_print_loop(responses)


def main():
    atlas = Atlas()
    
    atlas.listen()


if __name__ == '__main__':
    main()
