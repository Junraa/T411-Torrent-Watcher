T411 Torrent Watcher by Junraa
==============================

Welcome on the T411 Torrent Watcher project.

It should be simple to use. Everything is written
in search.py at the moment.


Configuration
--------------

Change the following main variables at the beginning of the *config.ini* file :

-   User: Your username on T411
-   Password: Your password on T411
-   Watch\_dir: Used with rtorrent at first, this directory is the one your torrent
will be saved in.
-   List\_dir: Directory in wich you should add a "TV Shows/" folder containing
files following this format.


Add your TV shows
-----------------

TV Shows files follow a yml format :

example : Arrow.yml

    name: Arrow
    query: Arrow
    seasons:
    - current: 24
      id: 1
      max: 23
    - current: 24
      id: 2
      max: 23
    - current: 20
      id: 3
      max: 23
    terms:
      language: VOSTFR Multi
      quality: 720 1080
      type: 2D

Please note that terms must match your torrent response to your query. They
are actually keywords that the script search in responses terms.

You can precise terms for a single season, they'll be taken in account instead
of the general ones.

The script will read this file and try to search for matching torrents, and
update the file if a matching torrent is found. It will increment the CurrentEpisode
number.

If the CurrentEpisode is 1, the script will first look for a complete Season.

The script will also loop once it has downloaded an episode and try to download
the following ones.

Install & Run
----------------------

Clone the project and configure the config.ini

`pip install -r requirements`

Create a cron to execute the script a often as you want

## requirements

* PyYAML
* requests
