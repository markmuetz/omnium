import os
import hashlib


class ResultsManager(object):
    DONE_FILE_TPL = '{}.{}.done'
    SAVE_FILE_TPL = '{}.{}'

    def __init__(self, computer_name, config):
        self.computer_name = computer_name
        self.config = config

    def key(self, args):
        return hashlib.sha1(''.join(map(str, args))).hexdigest()

    def get_filename(self, results_dir, node_name, out_ext):
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)

        save_file = os.path.join(results_dir,
                                 self.SAVE_FILE_TPL.format(node_name, out_ext))
        return save_file
