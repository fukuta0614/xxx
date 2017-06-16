from urllib.request import urlopen, urlretrieve
import datetime
import hashlib
import re
import os
from bs4 import BeautifulSoup
import multiprocessing as mp
from functools import partial
from multiprocessing.pool import ThreadPool


def download_fc2(target, uncensored=0):
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
    sys.stdout.write(title + '\n')
    sys.stdout.flush()
    file_name = folder_name + title + ".flv"
    try:
        urlretrieve(flv_url, file_name)
    except:
        return False

    with open(DOWNLOADED_FILE, "a") as f:
        f.write("{0}\n".format(target))

    sys.stdout.write(title + '\n')
    sys.stdout.flush()
    return True


def main(ranking_type=1):
    baseurl = "http://video.fc2.com/a/list.php?m=cont&page={}" + "&type={}".format(ranking_type)

    if os.path.exists(DOWNLOADED_FILE):
        with open(DOWNLOADED_FILE, "r") as f:
            downloaded = f.read().split('\n')
    else:
        downloaded = []

    r = urlopen(baseurl.format(1), timeout=10)
    soup = BeautifulSoup(r.read(), "lxml")
    links = soup.findAll("a")
    targets = set()

    regex = re.compile(r"(?:/a)?/content/(\w+)/?$")

    for link in links:
        url = link.get("href").split("&")[0]
        match = regex.search(url)
        if match is None:
            continue
        target = match.group(1)
        if target in downloaded:
            continue
        targets.add(target)
    # print(targets)
    pool = ThreadPool()  # mp.Pool()
    pool.map(download_fc2, targets)
    print('finished')


def main_uncensored():
    baseurl = "http://video.fc2.com/a/list.php?m=cont&page={}&type=1"

    with open(DOWNLOADED_FILE, "r") as f:
        downloaded = f.read().split('\n')

    regex = re.compile(r"http://video\.fc2\.com(?:/a)?/content/(\w+)/?$")
    targets = set()

    for p_num in range(1, 9):
        r = urlopen(baseurl.format(p_num), timeout=10)
        soup = BeautifulSoup(r.read(), "lxml")
        links = soup.findAll("a")

        for link in links:
            url = link.get("href").split("&")[0]
            match = regex.search(url)
            if match is None:
                continue
            target = match.group(1)
            if target in downloaded:
                continue
            targets.add(target)

    # print(targets)
    pool = mp.Pool()

    pool.map(partial(download_fc2, uncensored=1), targets)
    print('finished')


if __name__ == '__main__':

    import sys, io, argparse

    parser = argparse.ArgumentParser(description='fc2 video downloader')
    parser.add_argument('--uncensored', '-u', type=int, default=0,
                        help='if you want only uncensored video, set 1')
    args = parser.parse_args()

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    folder_name = datetime.datetime.today().strftime("%Y%m%d") + '/'

    DOWNLOADED_FILE = "downloaded.txt"

    try:
        os.mkdir(folder_name)
    except FileExistsError:
        print("already exist")

    if args.uncensored > 0:
        main_uncensored()
    else:
        main()
