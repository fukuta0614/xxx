# -*- coding: utf-8 -*-
from urllib.request import urlopen, urlretrieve
import datetime
import hashlib
import re
import os
from bs4 import BeautifulSoup
from functools import partial
import sys
import io
import curses
import time
import multiprocessing as mp
from selenium import webdriver
import threading

class Download(mp.Process):
    row = 0

    def __init__(self, title, url):
        mp.Process.__init__(self)
        self.title = title
        self.file_name = MOVIE_PATH + self.title + ".flv"
        self.url = url
        self.row_num = Download.row
        Download.row += 1

        # self.folder = folder
        # self.setDaemon(True)

    def reporthook(self, *a):
        percentage = round(100.0 * a[0] * a[1] / a[2], 2)
        p = "%.2f%%" % percentage
        stdscr.addstr(self.row_num + 1, 0, "{0} : {1}".format(self.title, p))
        stdscr.refresh()

    def run(self):
        try:
            urlretrieve(self.url, self.file_name, self.reporthook)
        except:
            return
        stdscr.addstr(self.row_num + 1, 0, "{0} : complete".format(self.title))
        with open(FOLDER_PATH + "movie_list.txt", "a") as f:
            f.write("{0}\n".format(self.title))


def download_movie(title, url, row):
    def reporthook(*a):
        percentage = round(100.0 * a[0] * a[1] / a[2], 2)
        p = "%.2f%%" % percentage
        stdscr.addstr(row + 1, 0, "{0} : {1}".format(title, p))
        stdscr.refresh()

    file_name = MOVIE_PATH + title + ".flv"
    urlretrieve(url, file_name, reporthook)

    stdscr.addstr(row + 1, 0, "{0} : complete".format(title))
    with open(FOLDER_PATH + "movie_list.txt", "a") as f:
        f.write("{0}\n".format(title))


def download_fc2(target, row, uncensored=0):

    if target.startswith('http'):
        match = re.search(r"http://video\.fc2\.com(?:/a)?/content/(\w+)/?$", target)
        if match is None:
            print('no match')
            return None
        target = str(match.group(1))

    FC2magick = '_gGddgPfeaf_gzyr'
    hash_target = (target + FC2magick).encode('utf-8')
    mini = hashlib.md5(hash_target).hexdigest()
    ginfo_url = 'http://video.fc2.com/ginfo.php?mimi=' + mini + '&v=' + target + '&upid=' + target + '&otag=1'

    soup = BeautifulSoup(urlopen(ginfo_url, timeout=3).read(), "lxml")
    try:
        filepath = soup.p.string
        flv_url = filepath.split('&')[0].split('=')[1] + '?' + filepath.split('&')[1]
        try:
            title = filepath.split('&')[14].split('=')[1]  # title(need encode)
            if len(title) < 4:
                title = filepath.split('&')[15].split('=')[1]
                # file_name = folder_name + title + ".flv"
        except:
            return None
    except:
        try:
            filepath = str(soup).replace(";", "").split("&amp")
            flv_url = filepath[0].split('=')[1] + '?' + filepath[1]
            title = filepath[14].split('=')[1]
        except:
            return None

    if not flv_url.startswith('http'):
        # print('flv_url error')
        return
    if uncensored > 0 and not "無" in title:
        # print('not uncensored')
        return


    def reporthook(*a):
        # percentage = round(100.0 * a[0] * a[1] / a[2], 2)
        # p = "%.2f%%" % percentage
        t = int(50 * a[0] * a[1] / a[2])
        stdscr.addstr(2 * row + 1, 0, '[' + '#'*t + '.'*(50-t) + ']')
        stdscr.refresh()

    stdscr.addstr(2 * row, 0, title)
    file_name = folder_name + title + ".flv"
    try:
        urlretrieve(flv_url, file_name, reporthook)
    except:
        return False
    stdscr.addstr(2 * row + 1, 0, '[' + '#'*50 + ']' + "complete")

    with open(DOWNLOADED_FILE, "a") as f:
        f.write("{0}\n".format(target))

    return True


def main(ranking_type=1):

    baseurl = "http://video.fc2.com/a/list.php?m=cont&page=1" + "&type={}".format(ranking_type)
    baseurl = 'http://video.fc2.com/a/recentpopular.php?page=1'

    if os.path.exists(DOWNLOADED_FILE):
        with open(DOWNLOADED_FILE, "r") as f:
            downloaded = f.read().split('\n')
    else:
        downloaded = []

    # print(downloaded)
    r = urlopen(baseurl, timeout=10)
    soup = BeautifulSoup(r.read(), "lxml")
    links = soup.findAll("a")
    targets = set()

    regex = re.compile(r"http://video\.fc2\.com(?:/a)?/content/(\w+)/?$")

    for link in links:
        url = link.get("href").split("&")[0]
        match = regex.search(url)
        if match is None:
            continue
        target = match.group(1)
        if target in downloaded:
            continue
        targets.add(target)


    try:
        global stdscr
        stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()

        ranking_type_str = ["weekly", "half-yearly", "yearly"]
        stdscr.addstr(0, 0, "collect videos from fc2 {} ranking".format(ranking_type_str[ranking_type - 1]))

        # for i, t in enumerate(movie_list):
        #     stdscr.addstr(i + 1, 0, "{0} :".format(t[0]))
        # stdscr.refresh()

        jobs = []
        for i, target in enumerate(targets):
            p = threading.Thread(target=download_fc2, args=(target, i+1))
            jobs.append(p)
            p.start()

        for j in jobs:
            j.join()
    finally:
        curses.endwin()


def old_threading():
    movie_list = []
    process_num = 4
    thread_list = set()
    while True:
        if len(thread_list) < process_num and len(movie_list) > 0:
            target = movie_list.pop(0)
            t = Download(*target)
            t.start()
            thread_list.add(t)
        set_new = set()
        for thread in thread_list:
            if thread.is_alive():
                set_new.add(thread)
        thread_list = set_new
        if len(thread_list) == 0:
            break
        time.sleep(3)


if __name__ == '__main__':

    import sys, io, argparse

    parser = argparse.ArgumentParser(description='fc2 video downloader')
    parser.add_argument('--uncensored', '-u', type=int, default=0,
                        help='if you want only uncensored video, set 1')
    parser.add_argument('--ranking_type', '-r', type=int, default=1,
                        help='type of ranking  weekly -> 1 half-yearly -> 2 yearly -> 3')
    args = parser.parse_args()

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    folder_name = datetime.datetime.today().strftime("%Y%m%d") + '/'

    DOWNLOADED_FILE = "downloaded.txt"



    try:
        os.mkdir(folder_name)
    except FileExistsError:
        print("already exist")

    main()

    # if args.uncensored > 0:
    #     main_uncensored()
    # else:
    #     main()
