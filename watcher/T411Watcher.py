import requests
import sys
import logging
from enum import Enum

class Categories(Enum):
    tv_shows = "433"
    movies = "631"


class Watcher(object):
    def search(self, episode=None, season=None, terms=None, seasonterms=None):
        pass

class T411Watcher(Watcher):


    def __init__(self, user, password, t411):
        self.password = password
        self.user = user
        self.t411 = t411

    def auth(self):
        req = requests.post(self.t411 + "/auth", {'username': self.user, 'password': self.password})
        logging.info("Authentified with uid : {}, token : {}".format(req.json()["uid"], req.json()["token"]))
        return req

    def get_userinfo(self, id, token):
        req = requests.get(self.t411 + "/users/profile/{}".format(id), headers={"Authorization": token})
        logging.debug(req.content)
        return req

    def get_categories(self, token):
        req = requests.get(self.t411 + "/categories/tree", headers={"Authorization": token})
        logging.info("Categories :")
        json = req.json()
        categories = {}
        for tmp in json:
            try:
                name = json[tmp]['name']
                logging.info("   " + name + " : " + tmp)
                categories[name] = tmp
            except KeyError as e:
                logging.error("   " + "No field 'name' for : {} == {}".format(tmp, json[tmp]))

        return categories, json

    def download(self, id, token):
        req = requests.get(self.t411 + "/torrents/download/" + id, headers={"Authorization": token})
        return req.content

    def search(self, episode=None, season=None, terms=None, seasonterms=None):
        if terms["query"] is None:
            sys.stderr.write("Please enter at least a torrent name")
            return None
        logging.info("Searching for {}, Season {}, Episode {}".format(terms["name"], season, episode))
        # authentification token
        authentification = self.auth()
        token = authentification.json()['token']
        query = terms["query"].replace(" ", "-")

        # Format query if number are inferior to 10
        if season is not None:
            season_str = (season.__str__() if season >= 10 else "0{}".format(season))
        if episode is not None:
            episode_str = (episode.__str__() if episode >= 10 else "0{}".format(episode))

        # Choose category if Movies or TV Shows
        cat = Categories.tv_shows
        if episode is None and season is None:
            cat = Categories.movies

        # Launch query depending on the category
        req = requests.get("{}/torrents/search/{}&cat={}".format(self.t411, query, cat), headers={"Authorization": token})
        json = req.json()
        logging.info("Fetching {} torrents".format(json["total"]))
        if (json["total"] == 0):
            return None

        # Since we get them 10 by 10...
        torrents = [torrent for torrent in json["torrents"]]
        offset = 10
        try:
            while len(json["torrents"]) > 0:
                req = requests.get(
                    "{}/torrents/search/{}&cat={}&offset={}".format(self.t411, query, cat, offset),
                    headers={"Authorization": token})
                json = req.json()
                for tor in json["torrents"]:
                    torrents.append(tor)
                offset += 10
        except Exception as e:
            logging.error('Error while parsing response {}'.format(e))

        # Calculating average seeders number
        moy = 0.00
        # Filter in case of special cases where torrent is not a dic
        torrents = [torrent for torrent in torrents if type(torrent) is dict]
        for torrent in torrents:
            try:
                moy += float(torrent["seeders"])
            except Exception as e:
                logging.error("wrong seeders term : {}".format(torrent))
        moy = moy / len(torrents)
        logging.info("Seeders average : {}".format(moy))
        torrents = sorted([x for x in torrents if float(x["seeders"]) > moy], key=lambda torr: float(torr["seeders"]),
                          reverse=True)

        # Usual filter, like quality, languages, etc.
        currentterms = terms["terms"]
        if "terms" in seasonterms:
            currentterms = seasonterms["terms"]

        hdtorrents = []
        for i in torrents:
            req = requests.get("{}/torrents/details/{}".format(self.t411, i["id"]), headers={"Authorization": token})
            json = req.json()
            try:
                if ((set(json["terms"]["Vidéo - Qualité"].split()) & set(currentterms["quality"].split())) or currentterms["quality"] is None):
                    hdtorrents.append((i, json["terms"]))

            except Exception as keyerror:
                logging.error("Error {} : {}\n".format(keyerror, currentterms))

        torrents = hdtorrents

        torrents = [hd for hd in torrents if ((set(hd[1]["Vidéo - Langue"].split()) & set(currentterms["language"].split())) or currentterms["language"] is None) \
                    and ((set(hd[1]["Vidéo - Type"].split()) & set(currentterms["type"].split())) or currentterms["type"] is None)]

        # If looking for a TV Shows, filter season and episode
        # Filter to avoid exception since T411 results may sometimes be weird
        torrents = [hd for hd in torrents if
                    (type(hd) is list or type(hd) is tuple) and type(hd[1]) is dict and "SérieTV - Saison" in hd[1]
                    and "SérieTV - Episode" in hd[1]]
        try:
            if not (episode is None and season is None):
                if episode is None:
                    torrents = [hd for hd in torrents if ("Saison complète" in hd[1]["SérieTV - Episode"]) \
                                and season_str in hd[1]["SérieTV - Saison"]]
                else:
                    torrents = [hd for hd in torrents if (episode_str in hd[1]["SérieTV - Episode"]) \
                                and season_str in hd[1]["SérieTV - Saison"]]
        except KeyError as keyerror:
            logging.error("keyerror : {}".format(keyerror))
        if len(torrents) == 0:
            logging.info("No matching torrent")
            return None

        # return resulting torrent
        logging.info("Terms : {}".format(torrents[0][1]))
        torrent_res = self.download(torrents[0][0]["id"], token)
        return (torrents[0][0]["name"] + ".torrent", torrent_res)
