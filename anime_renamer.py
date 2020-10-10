import configparser

from functions import *


class AnimeRenamer(object):
    def __init__(self, config_file):
        config = configparser.ConfigParser()
        config.read(config_file)
        self.source_dir = config['DIR']['source']
        self.target_dir = config['DIR']['target']
        self.log_file = os.path.join(self.source_dir, config['LOG']['log_file'])
        create_file(self.log_file)

    def get_last_time(self):
        with open(self.log_file, 'r') as log:
            ctime = log.readline()
            if ctime == '':
                return None
            else:
                return ctime

    def update_log(self, path):
        with open(self.log_file, 'w') as log:
            log.writelines(path.ctime)

    def set_target_path(self, files, t_dir, title, season):
        prefix_idx = get_prefix_idx([f.name for f in files])
        for f in files:
            file_ext = get_file_ext(f.name)
            episode = get_episode(f.name[prefix_idx:])
            if episode:
                f.t_name = title + " S" + format(season, '02d') + "E" + episode + file_ext
                f.t_path = os.path.join(t_dir, f.t_name)
            else:
                f.t_name = f.name
                f.t_path = os.path.join(t_dir, f.t_name)

    def rename(self, s_dir):
        p_name = re.split('/', s_dir.path.replace(self.source_dir, '').strip('/'))[0]
        title = get_title(p_name)
        season = get_season(s_dir.name)
        if season == 0:
            season_dir = 'Special'
        else:
            season_dir = "Season " + str(season)
        t_dir = os.path.join(self.target_dir, title, season_dir)

        media_files = list_main_media_files(s_dir.path)
        self.set_target_path(media_files, t_dir, title, season)

        sub_files = list_sub_files(s_dir.path)
        self.set_target_path(sub_files, t_dir, title, season)

        print('Target dir: ' + t_dir)
        print('>>')
        print("Rename " + str(len(media_files)) + " media files:")
        for f in media_files:
            print(f.name + '  ====>>  ' + f.t_name)
        print('>>')
        print("Rename " + str(len(sub_files)) + " sub files:")
        for f in sub_files:
            print(f.name + '  ====>>  ' + f.t_name)
        print('>>')
        if click.confirm('Are you sure to rename these files?', default=True):
            print("Creating links ...")
            create_dir(t_dir)
            for f in media_files:
                f.symlink()
            for f in sub_files:
                f.copy()
            print("Create links successfully!")
            return True
        else:
            return False

    def process(self):
        new_dirs = list_dirs_new(self.source_dir, last_time=self.get_last_time())
        print('Find ' + str(len(new_dirs)) + ' new dirs:')
        for s_dir in new_dirs:
            print('---------------------------------------------------------------------------')
            s_dir_name = s_dir.path.replace(self.source_dir, '').strip('/')
            print('Processing dir:', s_dir_name)
            if not click.confirm('Continue?', default=True):
                if click.confirm('Ignore?', default=True):
                    self.update_log(s_dir)
                continue
            if self.rename(s_dir):
                print("Dir:", s_dir_name, "process finished")
                self.update_log(s_dir)
            else:
                print("Dir:", s_dir_name, "process cancelled")
                break
            print('---------------------------------------------------------------------------')


if __name__ == "__main__":
    anime_renamer = AnimeRenamer('config.ini')
    anime_renamer.process()
