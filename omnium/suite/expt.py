import os
from configparser import ConfigParser
from glob import glob
from logging import getLogger

from omnium.omnium_errors import OmniumError

logger = getLogger('om.expt')


class ExptList(list):
    def __init__(self, suite):
        self._suite = suite
        self.expt_datam_dir_fmt = self._suite.settings.get('expt_datam_dir', None)
        self.expt_dataw_dir_fmt = self._suite.settings.get('expt_dataw_dir', None)
        self.config_has_required_info = self.expt_datam_dir_fmt and self.expt_dataw_dir_fmt

    def find(self, expt_names):
        if not self.config_has_required_info:
            logger.warning('Required ExptList information not in config')
            logger.warning('Needs expt_datam_dir, expt_dataw_dir')
            return

        for expt_name in expt_names:
            self.append(Expt(self._suite, self, expt_name))

    def find_all(self):
        if not self.config_has_required_info:
            logger.warning('Required ExptList information not in config')
            logger.warning('Needs expt_datam_dir, expt_dataw_dir')
            return
        expt_names = []
        # Check assumption about expt dir is that expt name comes last.
        assert (os.path.split(self.expt_datam_dir_fmt.format(expt='DUMMY_EXPT_NAME'))[-1] ==
                'DUMMY_EXPT_NAME')
        expt_datam_dir_glob = os.path.join(self._suite.suite_dir,
                                           self.expt_datam_dir_fmt.format(expt='*'))
        logger.debug('using glob: {}', expt_datam_dir_glob)
        expt_datam_dirs = sorted(glob(expt_datam_dir_glob))
        for expt_datam_dir in [d for d in expt_datam_dirs if os.path.isdir(d)]:
            expt_name = os.path.split(expt_datam_dir)[-1]
            logger.debug('found expt: {}', expt_name)
            expt_names.append(expt_name)
        self.find(expt_names)

    def get(self, expt_name):
        for expt in self:
            if expt_name == expt.name:
                return expt
        raise OmniumError('No expt with name {}'.format(expt_name))


class Expt:
    def __init__(self, suite, expt_list, name):
        self._suite = suite
        self._expt_list = expt_list
        self.name = name
        self._config = None

        expt_datam_dir_fmt = self._expt_list.expt_datam_dir_fmt
        expt_dataw_dir_fmt = self._expt_list.expt_dataw_dir_fmt
        self.datam_dir = os.path.join(suite.suite_dir, expt_datam_dir_fmt.format(expt=name))
        expt_dataw_dir_glob = os.path.join(suite.suite_dir,
                                           expt_dataw_dir_fmt.format(cycle_timestamp='*',
                                                                     expt=name))
        if not os.path.exists(self.datam_dir):
            logger.warning('expt datam dir does not exist: {}', self.datam_dir)
        self.dataw_dirs = sorted(glob(expt_dataw_dir_glob))
        if not self.dataw_dirs:
            logger.warning('expt dataw dirs not found: {}', expt_dataw_dir_glob)

        if self.dataw_dirs:
            self.rose_app_run_conf_file = os.path.join(self._suite.suite_dir,
                                                       self.dataw_dirs[0], 'rose-app-run.conf')
            if os.path.exists(self.rose_app_run_conf_file):
                if self._suite.check_filename_missing(self.rose_app_run_conf_file):
                    logger.warning('expt rose-app-run.conf missing: {}',
                                   self.rose_app_run_conf_file)
            else:
                logger.warning('expt rose-app-run.conf not found: {}',
                               self.rose_app_run_conf_file)
        else:
            self.rose_app_run_conf_file = None
            logger.warning('expt rose-app-run.conf not found as no dataw_dirs')

    @property
    def has_um_config(self):
        return self.rose_app_run_conf_file is not None

    @property
    def model_type(self):
        model_type = self.um_config['namelist:model_domain'].getint('model_type')
        types = {1: 'global_model',
                 2: 'LAM_classic',
                 3: 'LAM_EW_cyclic',
                 4: 'LAM_bicyclic',
                 5: 'SCM',
                 6: 'SSFM'}
        return types[model_type]

    @property
    def dx(self):
        return self.um_config[self._namelist_idealised].getfloat('delta_xi1')

    @property
    def dy(self):
        return self.um_config[self._namelist_idealised].getfloat('delta_xi2')

    @property
    def dt(self):
        return (self.um_config['namelist:nlstcgen'].getfloat('secs_per_periodim') /
                self.um_config['namelist:nlstcgen'].getfloat('steps_per_periodim'))

    @property
    def nx(self):
        return self.um_config['namelist:nlsizes'].getint('global_row_length')

    @property
    def ny(self):
        return self.um_config['namelist:nlsizes'].getint('global_rows')

    @property
    def lx(self):
        return self.dx * self.nx

    @property
    def ly(self):
        return self.dy * self.ny

    @property
    def um_version(self):
        if not self._config:
            # Force load.
            _ = self.um_config
        return self._um_version

    @property
    def um_config(self):
        if not self.rose_app_run_conf_file:
            raise OmniumError('{} has no config file'.format(self))
        if not self._config:
            cp = ConfigParser()
            with open(self.rose_app_run_conf_file, 'r') as f:
                split_first_line = f.readline().split('=')
                assert split_first_line[0] == 'meta'
                # version looks like: um-atmos/vn11.0
                version = split_first_line[1].strip()
                self._um_version = tuple([int(v) for v in version.split('/')[-1][2:].split('.')])
                if self._um_version >= (10, 9):
                    self._namelist_idealised = 'namelist:recon_idealised'
                else:
                    self._namelist_idealised = 'namelist:idealise'
                second_line = f.readline()
                assert second_line.strip() == ''
                cp.read_file(f)
            self._config = cp
        return self._config

    def __str__(self):
        return 'Expt: {} - {}'.format(self._suite.suite_dir, self.name)
