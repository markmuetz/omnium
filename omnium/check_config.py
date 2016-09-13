"""Perform consistency checks on config"""
import sys
import imp
from collections import OrderedDict as odict

from dict_printer import pprint

from stash import Stash


class Req(object):
    def __init__(self, valname=None, value=None,
                 allowed=[], xref=None, valtype=None,
                 optional=False):
        self.valname = valname
        self.value = value
        self.allowed = allowed
        self.xref = xref
        self.valtype = valtype
        self.optional = optional

    def check(self, section):
        if self.valname:
            return section[self.valname] == self.value
        else:
            return True


CONFIG_SCHEMA = odict([
    ('settings', {'type': 'dict',
                  'keys': {
                      'ignore_warnings': Req(valtype=bool, optional=True),
                      'ignore_commands': Req(optional=True),
                      'console_log_level': Req(optional=True),
                      'file_log_level': Req(optional=True),
                      'disable_colour_log_output': Req(valtype=bool, optional=True),
                      }
                  }),
    ('computer_name', {'type': 'one',
                       'one': Req(xref='computers')}),
    ('computers', {'type': 'many',
                   'each': {
                       'remote': Req(optional=True),
                       'remote_address': Req(optional=True),
                       'remote_path': Req(optional=True),
                       'dirs': Req(),
                       }
                   }),
    ('batches', {'type': 'many',
                 'each': {
                     'index': Req(),
                     }
                 }),
    ('groups', {'type': 'many',
                'each': {
                    'type': Req(allowed=['init', 'group_process', 'nodes_process']),
                    'base_dir': Req(),
                    'batch': Req(xref='batches'),
                    'filename_glob': Req('type', 'init'),
                    'from_group': Req('type', 'group_process', xref='groups'),
                    'process': Req('type', 'group_process'),
                    'nodes': Req('type', 'nodes_process', xref='nodes'),
                    }
                }),
    ('nodes', {'type': 'many',
               'each': {
                   'type': Req(allowed=['from_nodes', 'from_group']),
                   'from_nodes': Req('type', 'from_nodes', xref='nodes'),
                   'from_group': Req('type', 'from_group', xref='groups'),
                   'variable': Req('type', 'from_group', xref='variables'),
                   'process': Req(),
                   }
               }),
    ('variables', {'type': 'many',
                   'each': {
                       'section': Req(valtype=int),
                       'item': Req(valtype=int),
                       }
                   }),
    ('process_options', {'type': 'any',
                         'each': {}
                         }),
    ])


class ConfigError(Exception):
    def __init__(self, message, hint):
        self.message = message
        if hint:
            self.hint = '  -' + hint
        else:
            self.hint = ''

    def __str__(self):
        return self.message


class ConfigChecker(object):
    @staticmethod
    def load_config(config_path='omni_conf.py'):
        # Stops .pyc file from being created.
        sys.dont_write_bytecode = True
        config_module = imp.load_source('omni_conf', config_path)
        sys.dont_write_bytecode = False

        settings = [d for d in dir(config_module) if d[:2] not in ['__']]
        config = dict((s, getattr(config_module, s)) for s in settings)
        return config

    def __init__(self, config, process_classes, raise_errors=True, warnings_as_errors=False):
        self.config = config
        self.process_classes = process_classes
        self.raise_errors = raise_errors
        self.warnings_as_errors = warnings_as_errors
        self.warnings = []
        self.errors = []

    def run_checks(self):
        self.schema_checks()
        self.xref_dir_checks()
        self.xref_checks()
        self.process_checks()
        self.variable_checks()
        self.computer_name_checks()

        return self.warnings, self.errors

    def _add_warning(self, msg):
        if self.warnings_as_errors:
            self._add_error(msg, 'Warning as Error')
        self.warnings.append(msg)

    def _add_error(self, msg, hint=None):
        error = ConfigError(msg, hint)
        self.errors.append(error)
        if self.raise_errors:
            raise error

    def schema_checks(self):
        for secname in CONFIG_SCHEMA.keys():
            if secname not in self.config:
                msg = 'Required section "{}" not present'.format(secname)
                self._add_error(msg)

        for secname, secschema in CONFIG_SCHEMA.items():
            conf_section = self.config[secname]

            if secschema['type'] == 'one':
                pass
            elif secschema['type'] == 'dict':
                for seckey, req in secschema['keys'].items():
                    if seckey not in conf_section and not req.optional:
                        msg = 'Missing value: "{}" not present in {}'.format(seckey, secname)
                        self._add_error(msg)
                for conf_key in conf_section.keys():
                    if conf_key not in secschema['keys']:
                        msg = 'Unrequired value in {}: "{}: {}"'\
                              .format(secname, conf_key, conf_section[conf_key])
                        self._add_warning(msg)

            if secschema['type'] == 'many':
                secvals = secschema['each']

                for conf_seckey, conf_secvalues in conf_section.items():
                    dont_check = []
                    for key, req in secvals.items():
                        # Check all config_secvalues have the required non-optional keys.
                        if req.valname and req.valname not in conf_secvalues and not req.optional:
                            msg = '{}:{} Required value "{}" not present'\
                                  .format(secname, conf_seckey, req.valname)
                            self._add_error(msg)
                            dont_check.append(key)

                    for key, req in secvals.items():
                        required = req.check(conf_secvalues)
                        if required and key not in conf_secvalues and not req.optional:
                            msg = '{}:{} Required value "{}" not present'\
                                  .format(secname, conf_seckey, key)
                            hint = None
                            if req.valname:
                                hint = 'required if {} == {}'.format(req.valname, req.value)
                            self._add_error(msg, hint)
                        else:
                            if req.allowed and conf_secvalues[key] not in req.allowed:
                                msg = '{}:{} "{}: {}" not an allowed value'\
                                      .format(secname, conf_seckey, key, conf_secvalues[key])
                                hint = 'must be one of {}'.format(', '.join(req.allowed))
                                self._add_error(msg, hint)
                        if req.valtype:
                            if type(conf_secvalues[key]) is not req.valtype:
                                msg = 'Wrong type {}:{} value "{}" is {}, should be {}'\
                                      .format(secname, conf_seckey, key,
                                              type(conf_secvalues[key]), req.valtype)
                                self._add_error(msg)

                    for key in conf_secvalues.keys():
                        if key not in secvals:
                            msg = '{}:{} Unknown value "{}: {}"'\
                                  .format(secname, conf_seckey, key, conf_secvalues[key])
                            self._add_warning(msg)
                        else:
                            req = secvals[key]
                            required = req.check(conf_secvalues)
                            if not required:
                                msg = '{}:{} Unrequired value "{}: {}"'\
                                      .format(secname, seckey, key, conf_secvalues[key])
                                self._add_warning(msg)

    def xref_dir_checks(self):
        for comp in self.config['computers'].values():
            for groupname, group in self.config['groups'].items():
                base_dir = group['base_dir']
                if base_dir not in comp['dirs']:
                    msg = 'base_dir XRef {0} missing from {1}'\
                          .format(base_dir, groupname)
                    self._add_error(msg)

    def xref_checks(self):
        for secname, secschema in CONFIG_SCHEMA.items():
            conf_section = self.config[secname]
            if secschema['type'] == 'many':
                secvals = secschema['each']
                for key, req in secvals.items():
                    if not req.xref:
                        continue

                    for conf_seckey, conf_secvalues in conf_section.items():
                        if key not in conf_secvalues:
                            continue

                        conf_vals = conf_secvalues[key]
                        if type(conf_vals) is str:
                            if conf_vals not in self.config[req.xref]:
                                msg = 'XRef {0} missing from {3}: {1}:{0}:{2}'\
                                      .format(key, conf_seckey, conf_vals, secname)
                                self._add_error(msg)
                        else:
                            for conf_val in conf_vals:
                                if conf_val not in self.config[req.xref]:
                                    msg = 'XRef {0} missing from {3}: {1}:{0}:{2}'\
                                          .format(key, conf_seckey, conf_val, secname)
                                    self._add_error(msg)

    def process_checks(self):
        errors = []
        for groupname, groupsec in self.config['groups'].items():
            if groupsec['type'] == 'group_process':
                if groupsec['process'] not in self.process_classes:
                    msg = 'Process not found from group: {}:process:{}'\
                          .format(groupname, groupsec['process'])
                    hint = 'available processes are:\n    {}'\
                           .format('\n    '.join(self.process_classes.keys()))
                    self._add_error(msg, hint)

        for nodename, nodesec in self.config['nodes'].items():
            if nodesec['process'] not in self.process_classes:
                msg = 'Process not found from node: {}:process:{}'\
                      .format(nodename, nodesec['process'])
                hint = 'available processes are:\n    {}'\
                       .format('\n    '.join(self.process_classes.keys()))
                self._add_error(msg, hint)

    def variable_checks(self):
        stash = Stash()
        for varname, varsec in self.config['variables'].items():
            if varsec['section'] not in stash:
                msg = 'Variable section not found in stash: {}:section:{}'\
                      .format(varname, varsec['section'])
                self._add_error(msg)
                continue
            if varsec['item'] not in stash[varsec['section']]:
                msg = 'Variable item not found in stash section {}: {}:item:{}'\
                      .format(varsec['section'], varname, varsec['item'])
                self._add_error(msg)

    def computer_name_checks(self):
        computer_name = self.config['computer_name']
        if computer_name not in self.config['computers']:
            msg = 'Computer name not found in computers: {}'\
                  .format(computer_name)
            hint = 'available computers are:\n    {}'\
                   .format('\n    '.join(self.config['computers'].keys()))
            self._add_error(msg, hint)
