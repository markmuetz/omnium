import os
from glob import glob
from logging import getLogger

logger = getLogger('om.expt')


class ExptList(list):
    def __init__(self, suite):
        self._suite = suite
        self.expt_datam_dir_fmt = self._suite.suite_config['settings'].get('expt_datam_dir', None)
        self.expt_dataw_dir_fmt = self._suite.suite_config['settings'].get('expt_dataw_dir', None)
        self.config_has_required_info = self.expt_datam_dir_fmt and self.expt_dataw_dir_fmt

    def find(self, expt_names):
        if not self.config_has_required_info:
            logger.warning('Required information not in config')
            return

        for expt_name in expt_names:
            self.append(Expt(self._suite, self, expt_name))

    def find_all(self):
        if not self.config_has_required_info:
            logger.warning('Required information not in config')
            return
        expt_names = []
        # Check assumption about expt dir is that expt name comes last.
        assert (os.path.split(self.expt_datam_dir_fmt.format(expt='DUMMY_EXPT_NAME'))[-1] ==
                'DUMMY_EXPT_NAME')
        expt_datam_dir_glob = os.path.join(self._suite.suite_dir,
                                           self.expt_datam_dir_fmt.format(expt='*'))
        logger.debug('using glob: {}', expt_datam_dir_glob)
        expt_datam_dirs = glob(expt_datam_dir_glob)
        for expt_datam_dir in [d for d in expt_datam_dirs if os.path.isdir(d)]:
            expt_name = os.path.split(expt_datam_dir)[-1]
            logger.debug('found expt: {}', expt_name)
            expt_names.append(expt_name)
        self.find(expt_names)


class Expt:
    def __init__(self, suite, expt_list, name):
        self._suite = suite
        self._expt_list = expt_list
        self.name = name

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

    def __str__(self):
        return 'Expt: {} - {}'.format(self._suite.suite_dir, self.name)
