#!/usr/bin/env python3

import yaml
import os
import configparser
import concurrent.futures
import logging

import watcher.T411Watcher

categories = ["Movies", "TV Shows"]
t411 = ''
user = ''
password = ''
watch_dir = ''
list_dir = ''
myid = None

CONFIG_FILE = "/home/junraa/Projects/t411-torrent-watcher/config.ini"


def load_config():
    global t411, user, password, watch_dir, list_dir
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    t411 = config.get("GLOBAL", "API")
    user = config.get("CREDENTIALS", "User")
    password = config.get("CREDENTIALS", "Password")
    watch_dir = config.get("PREFERENCES", "Watch_dir")
    list_dir = config.get("PREFERENCES", "List_dir")


def listdir():
    return [file for file in os.listdir(os.path.join(list_dir, "TV Shows")) if ".swp" not in file]


def set_and_download(yml, season, watcher=watcher.T411Watcher.Watcher()):
    season_nb = int(season["id"])
    episodemax = int(season["max"])
    currentepisode = int(season["current"])
    logging.debug(
        "set_and_download for TV Show : {}, season : {}, episode : {}, max : {}".format(yml["name"], season_nb,
                                                                                        currentepisode, episodemax))
    if currentepisode > episodemax:
        return

    # Select correct episode (full season or precise episode)
    while currentepisode <= episodemax:
        res = watcher.search(season=int(season_nb), episode=(None if currentepisode == 1 else currentepisode),
                             terms=yml, seasonterms=season)
        if currentepisode == 1 and not res is None:
            currentepisode = episodemax
        if res is None and currentepisode == 1:
            res = watcher.search(season=int(season_nb), episode=1, terms=yml, seasonterms=season)
        if res is None:
            return

        currentepisode += 1

        resfile = open(os.path.join(watch_dir, res[0]), "wb")
        resfile.write(res[1])
        resfile.close()

        season["current"] = int(currentepisode)


def watch_and_download(watcher=None):
    for f in listdir():
        file = open(os.path.join(list_dir, "TV Shows", f), "r")
        yml_file = yaml.load(file)
        file.close()

        if "name" not in yml_file or yml_file["name"] is None:
            yml_file["name"] = yml_file["query"]
        if "query" not in yml_file or yml_file["query"] is None:
            yml_file["query"] = yml_file["name"]

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            for season in yml_file["seasons"]:
                logging.debug("Submitting {} to ThreadPoolExecutor".format(f))
                executor.submit(set_and_download, yml_file, season, watcher)

        file = open(os.path.join(list_dir, "TV Shows", f), "w")
        file.write(yaml.dump(yml_file, default_flow_style=False))
        file.close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    load_config()
    watcher = watcher.T411Watcher.T411Watcher(user, password, t411)
    watch_and_download(watcher)
