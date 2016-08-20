import os
import hashlib


class ResultsManager(object):
    DONE_FILE_TPL = '{}.nc.done'
    SAVE_FILE_TPL = '{}.nc'

    def __init__(self, config):
        self.config = config
        if not os.path.exists(config.settings.results_dir):
            os.makedirs(config.settings.results_dir)

    def key(self, *args):
        return hashlib.sha1(''.join(map(str, args))).hexdigest()

    def get_filename(self, *args):
        key = self.key(*args)
        save_file = os.path.join(self.config.settings.results_dir, 
                                 self.SAVE_FILE_TPL.format(key))
        return save_file
