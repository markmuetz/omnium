"""Perform consistency checks on config"""
from collections import OrderedDict as odict

from dict_printer import pprint
from processes import get_process_classes
from stash import stash

class Req(object):
    def __init__(self, valname=None, value=None, 
                       allowed=[], xref=None, valtype=None):
        self.valname = valname
        self.value = value
        self.allowed = allowed
        self.xref = xref
        self.valtype = valtype

    def check(self, section):
        if self.valname:
            return section[self.valname] == self.value
        else:
            return True


CONFIG_SCHEMA = odict([
    ('settings', {'type': 'dict',
                  'keys': {
                      'ignore_warnings': Req(valtype=bool)
        }
    }),
    ('computer_name', {'type': 'one',
                       'one': Req(xref='computers')}),
    ('computers', {'type': 'many',
        'each': {
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
        'each': { } 
    }),
])



class ConfigError(Exception):
    def __init__(self, message, hint):
        self.message = message
        self.hint = '  -' + hint

    def __str__(self):
        return self.message


class ConfigChecker(object):
    def __init__(self, args, config, raise_errors=True, warnings_as_errors=False):
        self.args = args
        self.config = config
        self.raise_errors = raise_errors
        self.warnings_as_errors = warnings_as_errors
        self.warnings = []
        self.errors = []

    def run_checks(self):
        self.schema_checks()
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
                for key in secschema['keys']:
                    if key not in conf_section:
                        msg = 'Missing value: "{}" not present in {}'.format(key, secname)
            if secschema['type'] == 'many':
                secvals = secschema['each']
                for conf_seckey, conf_secvalues in conf_section.items():
                    for key, req in secvals.items():
                        required = req.check(conf_secvalues)
                        if required and key not in conf_secvalues:
                            msg = '{}:{} Required value "{}" not present'.format(secname, conf_seckey, key)
                            hint = None
                            if req.valname:
                                hint = 'required if {} == {}'.format(req.valname, req.value)
                            self._add_error(msg, hint)
                        else:
                            if req.allowed and conf_secvalues[key] not in req.allowed:
                                msg = '{}:{} "{}: {}" not an allowed value'.format(secname, conf_seckey, key, conf_secvalues[key])
                                hint = 'must be one of {}'.format(', '.join(allowed))
                                self._add_error(msg, hint)
                        if req.valtype:
                            if type(conf_secvalues[key]) is not req.valtype:
                                msg = 'Wrong type {}:{} value "{}" is {}, should be {}'.format(secname, conf_seckey, key, type(conf_secvalues[key]), req.valtype)
                                self._add_error(msg)


                    for key in conf_secvalues.keys():
                        if key not in secvals:
                            msg = '{}:{} Unknown value "{}: {}"'.format(secname, conf_seckey, key, conf_secvalues[key])
                            self._add_warning(msg)
                        else:
                            req = secvals[key]
                            required = req.check(conf_secvalues)
                            if not required:
                                msg = '{}:{} Unrequired value "{}: {}"'.format(secname, seckey, key, conf_secvalues[key])
                                self._add_warning(msg)


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
                                msg = 'XRef {0} missing from {3}: {1}:{0}:{2}'.format(key, conf_seckey, conf_vals, secname)
                                self._add_error(msg)
                        else:
                            for conf_val in conf_vals:
                                if conf_val not in self.config[req.xref]:
                                    msg = 'XRef {0} missing from {3}: {1}:{0}:{2}'.format(key, conf_seckey, conf_val, secname)
                                    self._add_error(msg)

    def process_checks(self):
        process_classes = get_process_classes(self.args.cwd)
        errors = []
        for groupname, groupsec in self.config['groups'].items():
            if groupsec['type'] == 'group_process':
                if groupsec['process'] not in process_classes:
                    msg = 'Process not found from group: {}:process:{}'.format(groupname, groupsec['process'])
                    hint = 'available processes are:\n    {}'.format('\n    '.join(process_classes.keys()))
                    self._add_error(msg, hint)

        for nodename, nodesec in self.config['nodes'].items():
            if nodesec['process'] not in process_classes:
                msg = 'Process not found from node: {}:process:{}'.format(nodename, nodesec['process'])
                hint = 'available processes are:\n    {}'.format('\n    '.join(process_classes.keys()))
                self._add_error(msg, hint)


    def variable_checks(self):
        for varname, varsec in self.config['variables'].items():
            if varsec['section'] not in stash.stash_vars:
                msg = 'Variable section not found in stash: {}:section:{}'.format(varname, varsec['section'])
                self._add_error(msg)
                continue
            if varsec['item'] not in stash.stash_vars[varsec['section']]:
                msg = 'Variable item not found in stash section {}: {}:item:{}'.format(varsec['section'], varname, varsec['item'])
                self._add_error(msg)

        
    def computer_name_checks(self):
        computer_name = self.config['computer_name']
        if computer_name not in self.config['computers']:
            msg = 'Computer name not found in computers: {}'.format(computer_name)
            hint = 'available computers are:\n    {}'.format('\n    '.join(self.config['computers'].keys()))
            self._add_error(msg, hint)
