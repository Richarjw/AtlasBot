from difflib import SequenceMatcher
import copy
import json
from bs4 import BeautifulSoup
import requests
from selenium import webdriver

import spacy
nlp = spacy.load("en_core_web_sm")


def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()


browser = webdriver.PhantomJS(
    executable_path=".\\phantomjs\\bin\\phantomjs.exe")


showtimes = {
    'The Secret Life of Pets 2': "https://www.fandango.com/the-secret-life-of-pets-2-215649/movie-times",
    'Dark Phoenix': "https://www.fandango.com/dark-phoenix-208497/movie-times",
    'Aladdin (2019)': "https://www.fandango.com/aladdin-2019-214978/movie-times",
    'Rocketman': "https://www.fandango.com/rocketman-214718/movie-times",
    'Godzilla: King of the Monsters (2019)': "https://www.fandango.com/godzilla-king-of-the-monsters-2019-213136/movie-times",
    'Ma (2019)': "https://www.fandango.com/ma-2019-217254/movie-times",
    'Late Night (2019)': "https://www.fandango.com/late-night-2019-217760/movie-times",
    'Men in Black: International': "https://www.fandango.com/men-in-black-international-216273/movie-times",
}

movie_data = {}
result = {'movie': "UNK", 'time': 'UNK',
          'theater': 'UNK', 'ticket': "UNK", 'attending': "UNK"}


current_query = 'movie'
movie_chosen = False
time_chosen = False
theater_chosen = False

global potential_results
potential_results = []

# state = {'moviePicked': False, 'theaterPicked': False}

# STATES: Idle, Atlas-Request, User-Request, Atlas-Inform, User-Inform, Found
global STATE

STATE = 'Idle'


def inform(info):
    print("Inform - ", info)


def request(info):
    print("Request - ", info)


def request_from_user():
    return "User-Request"


def request_from_atlas():
    return "Atlas-Request"


def inform_from_user():
    return "User-Inform"


def inform_from_atlas():
    return "Atlas-Inform"


def idle():
    return "Idle"


def result_found():
    return "Found"


class StateManager(object):
    def __init__(self):
        self.movies = set([])
        self.theaters = set([])
        self.genres = set([])
        self.STATE = "Idle"
        self.result = {'movie': "UNK", 'time': 'UNK',
                       'theater': 'UNK', 'ticket': "UNK", 'attending': "UNK"}
        self.CURRENT_QUERY = 'movie'
        self.movie_data = []
        self.options = []
        with open('data.json') as json_file:
            movie_data = json.load(json_file)
            for key in movie_data.keys():
                self.movie_data.append(movie_data[key])
                self.movies.add(movie_data[key]['title'])
                self.theaters.add(movie_data[key]['theater'])
                for genre in movie_data[key]['genre']:
                    self.genres.add(genre)
                print(self.movie_data)

    def reset_query(self):
        self.STATE = "Idle"
        self.result = {'movie': "UNK", 'time': 'UNK',
                       'theater': 'UNK', 'ticket': "UNK", 'attending': "UNK"}
        self.CURRENT_QUERY = "movie"

    def check_cancel(self, input):
        return "stop" in input or "cancel" in input or "nevermind" in input

    def check_confirm(self, input):
        return "yes" in input or "yeah" in input or "yea" in input

    def check_incorrect(self, input):
        return "no" in input or "not really" in input

    def check_movie_query(self, input):
        return "movie" in input or "movies" in input or "showing" in input

    def action(self, input):
        response = "Hmm. Think this still needs work..."
        if self.check_cancel(input):
            self.set_next_state("Idle")
        if self.STATE == "Idle":
            self.set_next_state("User-Request")
            return self.handle_user_request(input)
        if self.STATE == "Atlas-Inform":
            self.set_next_state("User-Request")
            return self.handle_user_request(input)
        if self.STATE == "Atlas-Request":
            self.set_next_state("User-Inform")
            return self.handle_user_inform(input)
        if self.STATE == "Found":
            self.set_next_state("Idle")
            self.result['ticket'] = self.movie_data[0]['ticket']
            self.result['theater'] = self.movie_data[0]['theater']
            self.result['showtime'] = self.movie_data[0]['showtime']
            result = copy.deepcopy(self.result)
            self.reset_query()
            print("Ticket:\t" + result['ticket'])
            return "I have printed out a link for the {0}m showing of {1} at the {2}".format(result['showtime'],result['movie'],result['theater'])
        if self.STATE == "Error":
            self.reset_query()
            return "Looks like there isn't any available showtimes for that movie today."

    def set_next_state(self, new_state):
        self.STATE = new_state

    def handle_user_inform(self, input):
        self.set_next_state("Atlas-Request")
        if self.check_incorrect(input):
            if self.CURRENT_QUERY != "movie":
                self.reset_query()
                return "Okay, let me know if I can do anything else."
            self.CURRENT_QUERY = 'genre'
            return "Is there a specific genre you might want to see?"
        if self.check_confirm(input):
            # Check if the movie was already stated, if not, request from atlas for the movie name
            words = nlp(input)
            nouns = [chunk.text for chunk in words.noun_chunks]

            if len(nouns) == 0 and self.CURRENT_QUERY == "movie":
                self.set_next_state("Atlas-Request")
                return "Which movie did you want me to look into?"
            if len(nouns) == 0 and self.CURRENT_QUERY == "showtimes":
                self.set_next_state("Atlas-Request")
                return "Which showtime are you interested in?"
        if self.CURRENT_QUERY == 'movie':
            # Match for movie and remove results for other movies
            movie = self.inform(input)
            self.result['movie'] = movie
            self.narrow_search('title', movie)
            self.CURRENT_QUERY = "showtimes"
            self.set_next_state("Atlas-Inform")
            return "I will narrow my scope to the movie: " + movie + "... Do you want showtimes near you?"
        if self.CURRENT_QUERY == "showtimes":
            showtime = self.inform(input).replace('m', '')
            self.result['showtime'] = showtime
            self.narrow_search('showtime', showtime)
            self.CURRENT_QUERY = "theater"
            self.set_next_state("Atlas-Inform")
            if (len(self.movie_data) == 1):
                self.set_next_state("Found")
                return "I believe I have found a possible showtime for you to attend. Would you like to hear it?"
            return "Narrowing search to theaters with showtimes for {0} at {1}m... Would you like to hear the theater choices?".format(self.result['movie'], self.result['showtime'])
        if self.CURRENT_QUERY == "theater":
            theater = self.inform(input)
            self.result['theater'] = theater
            self.narrow_search('theater', theater)
            if (len(self.movie_data) == 1):
                self.set_next_state("Found")
                return "I believe I have found a possible showtime for you to attend. Would you like to hear it?"
            return "Narrowing search to showings of {0} for {1}m at the {2}... ".format(self.result['movie'], self.result['showtime'], self.result['theater'])

        elif self.CURRENT_QUERY == 'genre':
            # Match for genre and remove results for other genres
            print(input)
            return "I am checking for a specific genre"

    def narrow_search(self, variable, value):
        new = []
        for i in range(len(self.movie_data)):
            if (self.movie_data[i][variable] == value):
                new.append(self.movie_data[i])
        self.movie_data = new
        if len(self.movie_data) == 0:
            self.set_next_state("Error")
        elif len(self.movie_data) == 1:
            self.set_next_state("Found")
        print("Possibilities Remaining: ", len(self.movie_data))

    def handle_user_request(self, input):
        if self.check_movie_query(input):
            self.set_next_state("Atlas-Request")
            return self.list_movies()
        if self.CURRENT_QUERY == "showtimes":
            self.set_next_state("Atlas-Request")
            return self.list_available_showtimes()
        if self.CURRENT_QUERY == "theater":
            self.set_next_state("Atlas-Request")
            return self.list_theaters()
        else:
            return "Stuck in Handle User Request Function"

    def list_theaters(self):
        theaters = set([])
        for option in self.movie_data:
            theaters.add(option['theater'])
        response = "The available theaters are: "
        for theater in theaters:
            response += theater + ", "
        return response + "... Do any of these work for tonight?"

    def list_available_showtimes(self):
        showtimes = set([])
        for option in self.movie_data:
            showtimes.add(option['showtime'] + "m")
        response = "{0} is playing at: ".format(self.result['movie'])
        for showtime in list(showtimes):
            response += showtime + ", "
        self.set_next_state("Atlas-Request")
        self.options = showtimes
        return response + "... Do any of these work?"

    def inform(self, input):
        best_similarity = 0
        selected = ""
        for option in self.options:
            similarity = similar(input, option)
            if similarity > best_similarity:
                best_similarity = similarity
                selected = option
        return selected

    def list_movies(self):
        self.options = self.movies
        response = "Do any of these interest you? "
        for movie in self.movies:
            response += movie + ", "
        return response


class Movie(object):
    def __init__(self, title, url):
        self.title = title
        self.url = url

    def __str__(self):
        return "Movie\t" + self.title + "\t" + self.url

    def getTimes(self):
        browser = webdriver.PhantomJS(
            executable_path=".\\phantomjs\\bin\\phantomjs.exe")
        browser.get(self.url)
        html = browser.page_source
        soup = BeautifulSoup(html, 'html.parser')
        page = soup.find("div", id="page")
        mop = page.findAll("div")
        for m in mop:
            if m.has_attr("class") and m['class'] == ['mop__details-container']:
                moviedetails = m.find("section", class_="movie-details")
                movieshowtimes = m.findAll("ol")
                print(moviedetails)


class Theater(object):
    def __init__(self, name, url):
        self.name = name
        self.url = url
        print(self)

    def __str__(self):
        return "Theater:\t" + self.name + " | " + self.url

    def getShowtimes(self):
        page = requests.get(self.url)
        soup = BeautifulSoup(page.content, 'html.parser')
        print(soup.prettify())
        row = soup.find("section", class_="row")
        # for i in row.find_all("div"):
        #     if i.has_attr('class'):
        #         print(i['class'])


class Fandango(object):
    def __init__(self):
        self.url = "https://www.fandango.com"
        self.zipcode = "60062"
        self.movies = []
        self.theaters = []


def get_theaters():
    theat = []
    page = requests.get(
        "https://www.fandango.com/60062_movietimes")
    soup = BeautifulSoup(page.content, 'html.parser')
    l = soup.findAll("option")
    for i in l:
        # theaters.add(i.text)
        theat.append(
            Theater(i.text, "https://www.fandango.com" + i['value']))
    return theat


def get_movies():
    movies = []
    page = requests.get("https://www.fandango.com/moviesintheaters")
    soup = BeautifulSoup(page.content, 'html.parser')
    lst = soup.findAll("li", class_="visual-item")
    for tag in lst:
        url = tag.find("a", class_="visual-container")
        img = tag.find("img")
        if img.has_attr("title"):
            movies.append(get_movie_details(url['href'], img['title']))
    return movies


def get_movie_details(movieurl, title):
    info = {'title': title, 'release-date': '',
            'genre': [], 'rating': "", 'length': ''}
    page = requests.get(movieurl)
    soup = BeautifulSoup(page.content, 'html.parser')
    lst = soup.findAll("ul")
    for tag in lst:
        if tag.has_attr("class") and tag['class'] == ['movie-details__detail']:
            li = tag.findAll("li")
            for item in li:
                if item.has_attr("class") and item['class'] == ["movie-details__release-date"]:
                    info['release-date'] = item.text
                else:
                    if "," in item.text:
                        rating = item.text.replace(
                            "\"", "").split(',')[0].strip()
                        time = item.text.replace(
                            "\"", "").split(',')[1].strip()
                        info['rating'] = rating
                        info['length'] = time
                    elif item.text != "Released" and item.text != "Opens" and item.text != "":
                        info['genre'].append(item.text)
    return info

    # showtimes = get_movie_showtimes(
    #     "https://www.fandango.com" + tag['href'])
    # print(showtimes)


def get_movie_showtimes(movieurl):
    browser = webdriver.PhantomJS(
        executable_path=".\\phantomjs\\bin\\phantomjs.exe")
    dic = {}
    list_of_showtimes = []
    browser.get(movieurl)
    soup = BeautifulSoup(browser.page_source, 'html.parser')
    for tag in soup.findAll("div"):
        if tag.has_attr("class") and tag['class'] == ['theater__wrap']:
            theater = ""
            showtimes = []
            items = tag.findAll('a')
            # details = tag.find("a", class_="color-light")
            # print(details.text)
            for item in items:
                if item.has_attr("class") and item['class'] == ['color-light']:
                    theater = item.text
                elif item.has_attr("class") and item['class'] == ["btn", "showtime-btn", 'showtime-btn--available']:
                    list_of_showtimes.append(
                        {"theater": theater, 'showtime': item.text, 'ticket': item['href']})
            dic[theater] = showtimes
    print(list_of_showtimes)
    browser.quit()
    return list_of_showtimes


def initialize():
    count = 0
    theats = get_theaters()
    movs = get_movies()
    data = {}
    print("Initializing Movie Showtimes")
    for movie in movs:
        print(movie['title'])
        infos = get_movie_showtimes(showtimes[movie['title']])
        for info in infos:
            cp = copy.deepcopy(movie)
            cp['theater'] = info['theater']
            cp['showtime'] = info['showtime']
            cp['ticket'] = info['ticket']
            data[count] = cp
            count += 1
    with open('data.json', 'w') as fp:
        json.dump(data, fp)


if __name__ == '__main__':
    initialize()
