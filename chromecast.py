import time
import pychromecast
from pychromecast.controllers.youtube import YouTubeController
from pychromecast.controllers.spotify import SpotifyController
import signal
from threading import Event
import spotipy.util as util
import spotipy
import json

# Triggers program exit
shutdown = Event()


def signal_handler(x, y):
    shutdown.set()


# Listen for these signals
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)


class AtlasChromecast:
    def __init__(self, name):
        with open(".cache-headingtoduke@aol.com") as write_file:
            self.token = json.load(write_file)
        self.name = name
        self.cast = self.getChromecast(name)
        self.youtube = None
        self.addYoutubeController()

    def __str__(self):
        return "{0} ChromeCast".format(self.name)

    def getChromecast(self, name):
        chromecasts = pychromecast.get_chromecasts()
        cast = next(cc for cc in chromecasts if cc.device.friendly_name == name)
        print(cast)
        return cast

    def addYoutubeController(self):
        self.youtube = YouTubeHandler()
        self.cast.register_handler(self.youtube.controller)

    def pauseMedia(self):
        self.cast.media_controller.pause()

    def playYoutubeVideo(self, id):
        self.youtube.playYoutubeVideo(id)

    def playMedia(self):
        self.cast.media_controller.play()     

class YouTubeHandler:
    def __init__(self):
        self.controller = YouTubeController()

    def playYoutubeVideo(self, youtubeId):
        self.controller.play_video(youtubeId)

    def turnOff(self):
        self.controller.tear_down()
    def playNextVideo(self, youtubeId):
        self.controller.play_next(youtubeId)
def main():
    cc = AtlasChromecast("Den TV")
    # cc.playYoutubeVideo("FAAf5X1gB54")
    cc.pauseMedia()
    return

if __name__ == '__main__':
    main()
