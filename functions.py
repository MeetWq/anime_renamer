import os
import re
import time
import click
import shutil
import difflib
from random import choice

from os.path import basename, exists, getmtime, getsize, isdir, isfile, join, splitext

media_type = ['.mp4', '.avi', '.rmvb', '.wmv', '.mov', '.mkv', '.flv']
sub_type = ['.srt', '.ssa', '.ass']


class File(object):
    def __init__(self, path):
        self.path = path
        self.name = basename(path)
        self.size = getsize(path)
        self.t_path = ""
        self.t_name = ""

    def symlink(self):
        try:
            os.symlink(self.path, self.t_path)
        except FileExistsError:
            print("file " + self.t_name + "already exist!")

    def copy(self):
        try:
            shutil.copyfile(self.path, self.t_path)
        except FileExistsError:
            print("file " + self.t_name + "already exist!")


class Dir(object):
    def __init__(self, path):
        self.path = path
        self.name = basename(path)
        self.ctime = time.ctime(getmtime(path))
        self.time = time.mktime(time.strptime(self.ctime, "%a %b %d %H:%M:%S %Y"))

    def cmp_ctime(self, ctime):
        return self.time > time.mktime(time.strptime(ctime, "%a %b %d %H:%M:%S %Y"))


def is_media(name):
    return splitext(name)[-1] in media_type


def is_sub(name):
    return splitext(name)[-1] in sub_type


def create_file(file):
    if not exists(file):
        with open(file, 'w'):
            pass


def create_dir(d):
    if not exists(d):
        os.makedirs(d)


def list_dirs(path):
    return [join(path, d) for d in os.listdir(path) if isdir(join(path, d))]


def list_media_files(path):
    return [File(join(path, f)) for f in os.listdir(path) if isfile(join(path, f)) and is_media(f)]


def list_sub_files(path):
    return [File(join(path, f)) for f in os.listdir(path) if isfile(join(path, f)) and is_sub(f)]


def list_dirs_full(path):
    dirs = list_dirs(path)
    dirs_full = []
    for d in dirs:
        if len(list_media_files(d)) != 0:
            dirs_full.append(d)
        else:
            sub_dirs = list_dirs(d)
            for sub_d in sub_dirs:
                if len(list_media_files(sub_d)) != 0:
                    dirs_full.append(sub_d)
    return dirs_full


def list_dirs_new(path, last_time=None):
    dirs = list_dirs_full(path)
    dirs = [Dir(d) for d in dirs]
    if last_time:
        dirs = [d for d in dirs if d.cmp_ctime(last_time)]
    dirs.sort(key=lambda x: x.time)
    return dirs


def differ_from_others(file, files):
    prefix_idx = get_prefix_idx([f.name for f in files])
    differ_count = 0
    for i in range(10):
        if difflib.SequenceMatcher(None, file.name[prefix_idx:], choice(files).name[prefix_idx:]).quick_ratio() < 0.7:
            differ_count += 1
    if differ_count > 6:
        return True
    else:
        return False


def list_main_media_files(path):
    files = list_media_files(path)
    files.sort(key=lambda x: x.size, reverse=True)
    max_size = files[int(len(files) / 10)].size
    files = [f for f in files if f.size * 2 > max_size]
    files = [f for f in files if not differ_from_others(f, files)]
    return files


def get_file_ext(name):
    file_name, file_ext = splitext(name)
    additional_ext = splitext(file_name)[-1]
    if 0 < len(additional_ext) < 15:
        file_ext = additional_ext + file_ext
    return file_ext


def get_repeat_idx(str1, str2):
    idx = 0
    for i in range(min(len(str1), len(str2))):
        if str1[i] != str2[i]:
            break
        idx += 1
    return idx


def get_prefix_idx(name_list):
    if len(name_list) <= 1:
        return 0
    idx = []
    for i in range(len(name_list) - 1):
        idx.append(get_repeat_idx(name_list[i], name_list[i + 1]))
    min_idx = min(idx)
    return min_idx


def get_title(name):
    name = re.sub(r'\[.*?\](.*?)', lambda x: x.group(1), name)
    name = re.sub(r'\(.*?\)(.*?)', lambda x: x.group(1), name)
    name = re.sub(r'(.*?)\[.*?\].*', lambda x: x.group(1), name)
    name = re.sub(r'(.*?)\(.*?\).*', lambda x: x.group(1), name)
    name = name.strip()
    title = re.split(r'Season', name)[0]
    title = re.split(r'S\d+', title)[0]
    title = re.split(r' - ', title)[0]
    title = re.split(r'第\d+季', title)[0]
    title = re.split(r'720p', title)[0]
    title = re.split(r'1080p', title)[0]
    title = title.strip('[]. ')
    title = title.replace('.', ' ')
    if not click.confirm('The title is: ' + title, default=True):
        title = input("Please input title: ")
    return title


def get_season(name):
    patterns = [r".*?S(\d+).*",
                r".*?Season[ ._-]*(\d+).*",
                r".*?第(\d+)季.*"]
    season = 1
    for pattern in patterns:
        if re.match(pattern, name):
            season = int(re.match(pattern, name).groups()[0])
            break
    if click.confirm('The season is: ' + str(season), default=True):
        pass
    else:
        season = int(input("Please input season number: "))
    return season


def get_episode(name):
    name = name.lower().strip().strip('[').strip('.').strip('【').strip('#').strip('-').strip('_')
    patterns = [
        r"e(\d{1,2}[v.]\d{1,2}).*",
        r"ep(\d{1,2}[v.]\d{1,2}).*",
        r"第(\d{1,2}[v.]\d{1,2}).*",
        r"e(\d{1,2}).*",
        r"ep(\d{1,2}).*",
        r"第(\d{1,2}).*",
        r"(\d{1,2}[v.]\d{1,2}).*",
        r"(\d{1,2}).*",
    ]
    for pattern in patterns:
        if re.match(pattern, name):
            episode = re.sub(pattern, lambda x: x.group(1), name)
            if episode == '':
                continue
            if re.fullmatch(r'[0-9]+', episode):
                episode = format(int(episode), '02d')
            return episode
    return None
