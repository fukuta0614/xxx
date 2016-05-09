#!/usr/bin/env python

from PyQt4 import QtCore, QtGui
import time, re, hashlib, datetime
from urllib.request import urlopen, urlretrieve
from bs4 import BeautifulSoup


class FetchThread(QtCore.QThread):

    signal = QtCore.pyqtSignal(list)

    def __init__(self):
        QtCore.QThread.__init__(self)
        self.value = 0
        self.folder_name = datetime.datetime.today().strftime("%Y%m%d") + '/'

    def __del__(self):
        self.wait()

    def get_info(self, target):
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
            return None

        return title, flv_url

    def run(self):
        baseurl = 'http://video.fc2.com/a/recentpopular.php?page=1'
        r = urlopen(baseurl, timeout=5)
        soup = BeautifulSoup(r.read(), "lxml")
        links = soup.findAll("a")
        targets = set()

        regex = re.compile(r"http://video\.fc2\.com(?:/a)?/content/(\w+)/?$")

        movie_list = []
        for link in links:
            url = link.get("href").split("&")[0]
            match = regex.search(url)
            if match is None:
                continue
            target = match.group(1)
            if target in targets:
                continue
            result = self.get_info(target)
            if result is None:
                continue
            title, flv_url = result
            targets.add(target)
            movie_list.append((target, title, flv_url))

        self.signal.emit(list(movie_list))


class DownloadThread(QtCore.QThread):

    signal = QtCore.pyqtSignal(list)

    def __init__(self, movie_info, row):
        QtCore.QThread.__init__(self)
        self.row = row
        self.b = row.itemAt(0).widget()
        self.b.setText(movie_info[1] + '   downloading...')
        self.bar = row.itemAt(1).widget()
        self.movie_info = movie_info

    def __del__(self):
        self.wait()

    def reporthook(self,*a):
        percentage = round(100.0 * a[0] * a[1] / a[2], 2)
        self.bar.setValue(percentage)

    def run(self):
        file_name = folder_name + self.movie_info[1] + ".flv"
        urlretrieve(self.movie_info[2], file_name, self.reporthook)


class Window(QtGui.QWidget):

    def __init__(self, parent=None):
        super(Window, self).__init__(parent)

        self.grid = QtGui.QVBoxLayout()

        self.button_list = []

        self.setting_group = self.create_setting_group()
        self.download_group = self.create_download_group()

        self.grid.addWidget(self.setting_group)
        self.grid.addWidget(self.download_group)

        self.setLayout(self.grid)
        self.setWindowTitle("fc2_downloader")
        self.resize(480, 320)

    def create_setting_group(self):
        groupbox = QtGui.QGroupBox("Setting",self)

        ranking_type = QtGui.QLabel('Ranking type')
        ranking_type_button = QtGui.QComboBox(self)
        ranking_type_button.addItems(("weekly", "half-yearly", "yearly"))
        ranking_type_button.setCurrentIndex(0)
        # ranking_type_button.setEditable(True)
        # ranking_type_button.lineEdit().setReadOnly(True)
        # ranking_type_button.lineEdit().setAlignment(QtCore.Qt.AlignCenter)
        layout1 = QtGui.QHBoxLayout()
        layout1.addWidget(ranking_type)
        layout1.addWidget(ranking_type_button)

        uncensored = QtGui.QLabel('Uncensored')
        b1 = QtGui.QRadioButton("normal")
        b2 = QtGui.QRadioButton("only uncensored")
        bg1 = QtGui.QHBoxLayout()
        bg1.addWidget(b1)
        # bg1.addStretch(1)
        bg1.addWidget(b2)

        layout2 = QtGui.QHBoxLayout()
        layout2.addWidget(uncensored)
        layout2.addLayout(bg1)

        setting_layout = QtGui.QVBoxLayout()
        setting_layout.addLayout(layout1)
        setting_layout.addLayout(layout2)

        groupbox.setLayout(setting_layout)

        return groupbox

    def create_download_group(self):
        groupbox = QtGui.QGroupBox("download")

        btn_exec = QtGui.QPushButton(u'Fetch Movie Info')
        btn_exec.clicked.connect(self.execute)
        btn_download = QtGui.QPushButton(u'Download')
        btn_download.clicked.connect(self.download)
        buttons = QtGui.QHBoxLayout()
        buttons.addWidget(btn_exec)
        buttons.addWidget(btn_download)

        vbox = QtGui.QVBoxLayout()
        vbox.addLayout(buttons)

        groupbox.setLayout(vbox)

        return groupbox

    def execute(self):
        self.thread = FetchThread()

        self.thread.signal.connect(self.result_fetch)
        QtCore.QObject.connect(self.thread, QtCore.SIGNAL("finished()"), self.done)
        self.thread.start()

        return

    def result_fetch(self, movie_lists):

        groupbox = QtGui.QGroupBox("movie")
        vbox = QtGui.QVBoxLayout()

        self.row = []
        self.movie_lists = movie_lists
        for target, title, flv_url in movie_lists:
            b = QtGui.QCheckBox(title)
            b.setChecked(True)
            bar = QtGui.QProgressBar(self)
            bar.setValue(0)
            row = QtGui.QVBoxLayout()
            row.addWidget(b)
            row.addWidget(bar)

            self.row.append(row)
            vbox.addLayout(row)

        self.movie_num = len(self.button_list)

        groupbox.setLayout(vbox)
        self.grid.addWidget(groupbox)

    def done(self):
        # QtGui.QMessageBox.information(self, "Done!", "Done fetching posts!")
        print('done')

    def download(self):

        self.thread_list = []
        for i,row in enumerate(self.row):
            if row.itemAt(0).widget().isChecked():
                self.thread = DownloadThread(self.movie_lists[i], row)
                self.thread.start()
                self.thread_list.append(self.thread)





if __name__ == '__main__':

    import sys, os

    folder_name = datetime.datetime.today().strftime("%Y%m%d") + '/'

    try:
        os.mkdir(folder_name)
    except FileExistsError:
        print("already exist")

    app = QtGui.QApplication(sys.argv)
    clock = Window()
    clock.show()
    sys.exit(app.exec_())