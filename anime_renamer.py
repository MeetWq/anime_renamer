import os
import re
import click
import shutil
import configparser


def create_file(file):
    if not os.path.exists(file):
        with open(file, 'w'):
            pass


def create_dir(d):
    if not os.path.exists(d):
        os.makedirs(d)


def scan_dirs(source_dir, log_file, media_type):
    with open(log_file, 'r') as log:
        logs = log.readlines()
        logs = [line.strip() for line in logs]
    dirs = [d for d in os.listdir(source_dir) if os.path.isdir(os.path.join(source_dir, d))]
    dirs_full = []
    for d in dirs:
        sub_dirs = list_sub_dir(os.path.join(source_dir, d), media_type)
        if len(sub_dirs) == 0:
            dirs_full.append(d)
        else:
            for sub_dir in sub_dirs:
                dirs_full.append(sub_dir)
    new_dirs_full = [os.path.join(source_dir, d) for d in dirs_full if d not in logs]
    return new_dirs_full


def list_sub_dir(source_dir, media_type):
    name = os.path.basename(source_dir)
    files = [f for f in os.listdir(source_dir) if os.path.isfile(os.path.join(source_dir, f))
                and os.path.splitext(f)[-1] in media_type]
    if len(files) == 0:
        dirs = [os.path.join(name, d) for d in os.listdir(source_dir) if
                os.path.isdir(os.path.join(source_dir, d))]
        return dirs
    else:
        return []


def get_title(name):
    name = re.sub(r'\[.*?\](.*?)', lambda x: x.group(1), name)
    name = re.sub(r'\(.*?\)(.*?)', lambda x: x.group(1), name)
    name = re.sub(r'(.*?)\[.*?\].*', lambda x: x.group(1), name)
    name = re.sub(r'(.*?)\(.*?\).*', lambda x: x.group(1), name)
    name = name.strip()
    title = re.split(r'Season', name)[0]
    title = re.split(r'S\d+', title)[0]
    title = re.split(r' - ', title)[0]
    title = title.strip()
    title = title.strip('.')
    if click.confirm('The title is: ' + title, default=True):
        new_title = title
    else:
        new_title = input("Please input title: ")
    return title, new_title


def get_season(name):
    patterns = [r".*?S(\d+).*",
                r".*?Season[ ._-]*(\d+).*"]
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


def get_episode(name, title):
    patterns = [r".*?" + title + r".*?S\d+E(\d+).*",
                r".*?" + title + r".*?\[(\d+\.\d+)\].*",
                r".*?" + title + r".*?\[(\d+v\d+)\].*",
                r".*?" + title + r".*?\[(\d+).*?\].*",
                r".*?" + title + r".*? (\d+\.\d+) .*",
                r".*?" + title + r".*? (\d+v\d+) .*",
                r".*?" + title + r".*? (\d+) .*",
                r".*?" + title + r".*?S(\d+).*",]
    for pattern in patterns:
        if re.match(pattern, name):
            return re.sub(pattern, lambda x: x.group(1), name)
    return ''


def check_unfinished(source_dir):
    for f in os.listdir(source_dir):
        if f == "unfinished":
            return True
    return False


def rename(source_dir, target_dir, title, new_title, season, media_type, sub_type):
    source_files = [f for f in os.listdir(source_dir) if
                    os.path.isfile(os.path.join(source_dir, f))
                    and os.path.splitext(f)[-1] in media_type and title in f]
    origin_files = []
    target_files = []
    incorrect_files = []
    for f in source_files:
        file_name, file_ext = os.path.splitext(f)
        episode = get_episode(file_name, title)
        if episode != '':
            target_name = new_title + " S" + format(season, '02d') + "E" + episode + file_ext
            target_files.append(target_name)
            origin_files.append(f)
        else:
            incorrect_files.append(f)

    sub_files = [f for f in os.listdir(source_dir) if
                 os.path.isfile(os.path.join(source_dir, f)) and os.path.splitext(f)[-1] in sub_type]
    sub_origin = []
    sub_target = []
    for i in range(len(origin_files)):
        origin_name = os.path.splitext(origin_files[i])[0]
        for sub_file in sub_files:
            if origin_name in sub_file:
                sub_origin.append(sub_file)
                sub_ext = sub_file.replace(origin_name, '')
                target_name = os.path.splitext(target_files[i])[0]
                sub_target.append(target_name + sub_ext)

    print("origin files: ")
    for f in origin_files:
        print(f)
    print("renamed files: ")
    for f in target_files:
        print(f)
    print("incorrect files: ")
    for f in incorrect_files:
        print(f)
    if click.confirm('Are you sure to rename these files?: ', default=True):
        for i in range(len(target_files)):
            try:
                os.link(os.path.join(source_dir, origin_files[i]), os.path.join(target_dir, target_files[i]))
            except FileExistsError:
                print("file", target_files[i], "already exist!")
        for i in range(len(sub_target)):
            try:
                shutil.copyfile(os.path.join(source_dir, sub_origin[i]), os.path.join(target_dir, sub_target[i]))
            except FileExistsError:
                print("file", sub_target[i], "already exist!")
        print("Create hard links successfully")
        return True
    else:
        return False


def process():
    config = configparser.ConfigParser()
    config.read('config.ini')

    source_dir = config['DIR']['source']
    target_dir = config['DIR']['target']
    log_file_name = config['LOG']['name']
    log_file = os.path.join(source_dir, log_file_name)
    media_type = config['TYPE']['media_type'].split('|')
    sub_type = config['TYPE']['sub_type'].split('|')

    create_file(log_file)
    new_dirs = scan_dirs(source_dir, log_file, media_type)
    for s_dir in new_dirs:
        print('---------------------------------------------------------------------------')
        s_dir_name = s_dir.replace(source_dir, '').strip().strip('/')
        print('Processing dir:', s_dir_name)
        name = os.path.basename(s_dir)
        title, new_title = get_title(re.split('/', s_dir_name)[0])
        season = get_season(name)
        t_dir = os.path.join(target_dir, new_title, "Season " + str(season))
        if click.confirm('Target dir: ' + t_dir, default=True):
            print("Creating hard links")
            create_dir(t_dir)
            if rename(s_dir, t_dir, title, new_title, season, media_type, sub_type):
                if not check_unfinished(s_dir):
                    with open(log_file, 'a') as log:
                        log.writelines(s_dir_name + '\n')
            print("Dir:", s_dir_name, "process finished")
        else:
            print("Dir:", s_dir_name, "process cancelled")
        print('---------------------------------------------------------------------------')


if __name__ == "__main__":
    process()
