import os
import hashlib


class ResultsManager(object):
    DONE_FILE_TPL = '{}.{}.done'
    SAVE_FILE_TPL = '{}.{}'

    def __init__(self, computer_name, config):
        self.config = config
        self.results_dir = config['computers'][computer_name]['dirs']['results']
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)

    def key(self, args):
        return hashlib.sha1(''.join(map(str, args))).hexdigest()

    def get_filename(self, args, out_ext):
        key = self.key(args)
        save_file = os.path.join(self.results_dir,
                                 self.SAVE_FILE_TPL.format(key, out_ext))
        return save_file
