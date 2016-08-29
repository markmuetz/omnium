import os
import hashlib


class ResultsManager(object):
    DONE_FILE_TPL = '{}.{}.done'
    SAVE_FILE_TPL = '{}.{}'

    def __init__(self, config):
        self.config = config
        if not os.path.exists(config['settings']['dirs']['results']):
            os.makedirs(config['settings']['dirs']['results'])

    def key(self, args):
        return hashlib.sha1(''.join(map(str, args))).hexdigest()

    def get_filename(self, args, out_ext):
        key = self.key(args)
        save_file = os.path.join(self.config['settings']['dirs']['results'], 
                                 self.SAVE_FILE_TPL.format(key, out_ext))
        return save_file
