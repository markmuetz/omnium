import os
import hashlib

import iris


class ResultsManager(object):
    INFO_FILE_TPL = '{}.txt'
    SAVE_FILE_TPL = '{}.nc'


    def __init__(self, config):
        self.config = config
        if not os.path.exists(config.settings.results_dir):
            os.makedirs(config.settings.results_dir)


    def key(self, *args):
        return hashlib.sha1(''.join(map(str, args))).hexdigest()


    def has(self, *args):
        key = self.key(*args)
        save_file = self.SAVE_FILE_TPL.format(key)
        save_filename = os.path.join(self.config.settings.results_dir, save_file)

        return os.path.exists(save_filename)


    def load(self, *args):
        key = self.key(*args)

        save_file = self.SAVE_FILE_TPL.format(key)
        info_file = self.INFO_FILE_TPL.format(key)

        save_filename = os.path.join(self.config.settings.results_dir, save_file)
        info_filename = os.path.join(self.config.settings.results_dir, info_file)

        return iris.load(save_filename)


    def save(self, result, *args):
        key = self.key(*args)

        save_file = self.SAVE_FILE_TPL.format(key)
        info_file = self.INFO_FILE_TPL.format(key)

        save_filename = os.path.join(self.config.settings.results_dir, save_file)
        info_filename = os.path.join(self.config.settings.results_dir, info_file)
        iris.save(result, save_filename)
        with open(info_filename, 'w') as f:
            f.write('#####\n')
            f.writelines('\n'.join(map(str, args)))
            f.write('#####\n')
            f.write(result.__str__())
