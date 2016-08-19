import os
from collections import OrderedDict
from ConfigParser import ConfigParser


class Config(object):
    def __init__(self, name, config_filename=None, root=None):
        self.name = name
        if name == 'root':
            self.is_root = True
            self.config_filename = config_filename
            self.reload()
        else:
            self.is_root = False
            self.root = root
            self._storage = OrderedDict()


    def delete(self, attr):
        self._storage.pop(attr)
        if self.is_root:
            if not self.is_loading:
                self._cp.remove_section(attr)
        else:
            if not self.root.is_loading:
                self.root._cp.remove_option(self.name, attr)


    def options(self):
        if self.is_root:
            raise Exception('should only be called on section')
        return self._storage.keys()


    def read_section(self, sec):
        sec_config = Config(sec, root=self)
        for opt in self._cp.options(sec):
            if opt[:5] == 'bool_':
                sec_config.set(opt[5:], self._cp.getboolean(sec, opt))
            elif opt[:4] == 'int_':
                sec_config.set(opt[4:], self._cp.getint(sec, opt))
            elif opt[:4] == 'env_':
                sec_config.set(opt[4:], os.path.expandvars(self._cp.get(sec, opt)))

            sec_config.set(opt, self._cp.get(sec, opt))
        return sec_config


    def reload(self):
        self.is_loading = True

        self._storage = OrderedDict()
        self._cp = ConfigParser()
        self._cp.read(self.config_filename)

        for sec in self._cp.sections():
            sec_config = self.read_section(sec)
            self.set(sec, sec_config)

        self.is_loading = False


    def save(self):
        with open(self.config_filename, 'wb') as f:
            self._cp.write(f)


    def set(self, attr, value):
        self._storage[attr] = value
        if self.is_root:
            if not self.is_loading:
                self._cp.add_section(value)
        else:
            if not self.root.is_loading:
                self.root._cp.set(self.name, attr, value)


    def _get_key_value_list(self):
        return ['{}={}'.format(k, v) for k, v in self._storage.items()]


    def __getattr__(self, attr):
        if not attr in self._storage:
            raise AttributeError('{} has no attribute {}'.format(self, attr))
        return self._storage[attr]


    def __repr__(self):
        return 'CONFIG'


    def __str__(self):
        if self.is_root:
            full_repr = []
            for k, value in self._storage.items():
                full_repr.append('[{}]'.format(k))
                full_repr.extend(value._get_key_value_list())
                full_repr.extend([''])
            return '\n'.join(full_repr)
        else:
            full_repr = ['[{}]'.format(self.name)]
            full_repr.extend(self._get_key_value_list())
            return '\n'.join(full_repr)



def read_config(cwd, config_filename):
    config_filename = os.path.join(cwd, config_filename)
    if not os.path.exists(config_filename):
        msg = 'Could not find {} in current dir'.format(config_filename)
        raise Exception(msg)
    
    config = Config('root', config_filename)
    return config
