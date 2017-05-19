import os
import sys
from glob import glob
from collections import OrderedDict
from logging import getLogger

from configparser import ConfigParser

from omnium.analyzers import get_analysis_classes
from omnium.converters import CONVERTERS
from omnium.omnium_errors import OmniumError
from omnium.suite import Suite

logger = getLogger('omnium')


class RunControl(object):
    def __init__(self, data_type, expt, force=False):
        self.cylc_control = os.getenv('CYLC_CONTROL') == 'True'
        self.data_type = data_type
        self.expt = expt
        self.force = force

        logger.warn('Disabling Python warnings')
        import warnings
        warnings.filterwarnings("ignore")

    def _read_env(self):
        omnium_dataw_dir = os.getenv('DATAW')
        omnium_datam_dir = os.getenv('DATAM')
        suite_name = os.getenv('CYLC_SUITE_NAME')
        initial_cycle_point = os.getenv('CYLC_SUITE_INITIAL_CYCLE_POINT')
        work_dir = os.getenv('CYLC_SUITE_WORK_DIR')

        return omnium_dataw_dir, omnium_datam_dir, suite_name, initial_cycle_point, work_dir

    def _read_config(self, config_dir, config_filename='rose-app-run.conf'):
        config = ConfigParser()
        with open(os.path.join(config_dir, config_filename), 'r') as f:
            config.read_file(f)
        return config

    def setup(self):
        if self.cylc_control:
            # Running through cylc.
            (omnium_dataw_dir, omnium_datam_dir, suite_name,
             initial_cycle_point, work_dir) = self._read_env()

            self.suite_name = suite_name
            self.analyzers_dir = omnium_dataw_dir

            self.atmos_datam_dir = omnium_datam_dir
            self.atmos_dataw_dir = os.path.join(work_dir, initial_cycle_point, self.expt + '_atmos')

            self.config = self._read_config(omnium_dataw_dir)
        else:
            # Standalone - work out all paths based on suite's path and load config.
            suite = Suite()
            try:
                suite.check_in_suite_dir(os.getcwd())
            except OmniumError:
                logger.warn('Not in suite')
                return

            self.suite = suite

            self.suite_name = suite.name
            self.analyzers_dir = self.suite.omnium_analysis_dir

            self.atmos_datam_dir = os.path.join(self.suite.suite_dir,
                                                'share/data/history',
                                                self.expt)

            work_dir = os.path.join(self.suite.suite_dir, 'work')
            initial_cycle_point_dir = sorted(glob(os.path.join(work_dir, '*')))[0]
            initial_cycle_point = os.path.basename(initial_cycle_point_dir)

            self.atmos_dataw_dir = os.path.join(work_dir, initial_cycle_point, self.expt + '_atmos')

            conf_dir = os.path.join(self.suite.suite_dir, 'app/omnium')
            self.config = self._read_config(conf_dir, 'rose-app.conf')

    def check_setup(self):
        for attr in ['analyzers_dir', 'atmos_datam_dir', 'atmos_dataw_dir']:
            if not os.path.exists(getattr(self, attr)):
                logger.warn('Dir does not exist: {}'.format(attr))

    def print_setup(self):
        for attr in ['cylc_control', 'data_type', 'expt', 'suite_name', 'analyzers_dir',
                     'atmos_datam_dir', 'atmos_dataw_dir']:
            print('{}: {}'.format(attr, getattr(self, attr)))

    def run(self):
        self.gen_analysis_workflow()
        self.run_all()

    def convert_all(self, filename_globs, overwrite, delete):
        if self.data_type == 'datam':
            data_dir = self.atmos_datam_dir
        elif self.data_type == 'dataw':
            data_dir = self.atmos_dataw_dir

        filenames = []
        logger.info('Converting files like:')
        for filename_glob in filename_globs:
            logger.info('  ' + filename_glob)
            for filename in sorted(glob(os.path.join(data_dir, filename_glob))):
                if os.path.exists(filename + '.done'):
                    logger.debug('  Adding: {}'.format(filename))
                    filenames.append(filename)
                else:
                    logger.warn('  Not finished: {}'.format(filename))

        converter = CONVERTERS['ff2nc'](overwrite, delete)
        for filename in filenames:
            try:
                converter.convert(filename)
            except OmniumError as oe:
                logger.error('Could not convert {}'.format(filename))
                logger.error(oe)

        if not filenames:
            logger.warn('No files to convert')

    def gen_analysis_workflow(self):
        self.analysis_workflow = OrderedDict()

        config = self.config
        suite_name = self.suite_name
        data_type = self.data_type
        expt = self.expt

        settings_sec = '{}_settings'.format(data_type)
        runcontrol_sec = '{}_runcontrol'.format(data_type)

        settings = config[settings_sec]
        runcontrol = config[runcontrol_sec]

        convert = settings['convert_to_nc'] == 'True'
        overwrite = settings['overwrite'] == 'True'
        delete = settings['delete'] == 'True'
        filename_globs = settings['filenames'].split(',')
        if convert:
            self.convert_all(filename_globs, overwrite, delete)

        self.analysis_classes = get_analysis_classes(self.analyzers_dir)

        for ordered_analysis, enabled_str in sorted(runcontrol.items()):
            analysis = ordered_analysis[3:]
            enabled = enabled_str == 'True'
            if not enabled:
                continue
            if config.has_section(analysis):
                analyzer_config = config[analysis]
            else:
                raise OmniumError('NO CONFIG FOR ANALYSIS')

            if analysis not in self.analysis_classes:
                raise OmniumError('COULD NOT FIND ANALYZER: {}'.format(analysis))

            Analyzer = self.analysis_classes[analysis]
            logger.debug(Analyzer)

            filename_glob = analyzer_config.pop('filename')
            logger.debug(filename_glob)
            if data_type == 'dataw':
                data_dir = self.atmos_dataw_dir
                results_dir = self.atmos_dataw_dir

            elif data_type == 'datam':
                data_dir = self.atmos_datam_dir
                results_dir = self.atmos_datam_dir

            if analysis in self.analysis_workflow:
                raise OmniumError('{} already in analysis workflow'.format(analysis))

            logger.debug('Adding analysis: {}'.format(analysis))
            analyzer_args = [suite_name, expt, data_type, data_dir, results_dir]
            self.analysis_workflow[analysis] = (Analyzer, analyzer_args,
                                                analyzer_config, filename_glob)

        logger.debug(self.analysis_workflow.keys())

    def run_analysis(self, analysis):
        Analyzer, analyzer_args, analyzer_config, filename_glob = self.analysis_workflow[analysis]
        self._run_analyzer(Analyzer, analyzer_args, analyzer_config, filename_glob)

    def run_all(self):
        for (Analyzer, analyzer_args,
             analyzer_config, filename_glob) in self.analysis_workflow.values():
            self._run_analyzer(Analyzer, analyzer_args, analyzer_config, filename_glob)

    def _run_analyzer(self, Analyzer, analyzer_args, analyzer_config, filename_glob):
        suite_name, expt, data_type, data_dir, results_dir = analyzer_args

        if data_type == 'dataw':
            filenames = [filename_glob]
        elif data_type == 'datam':
            data_dir = self.atmos_datam_dir
            filenames = Analyzer.get_files(data_dir, filename_glob)

        logger.info('Running {} on {} files'.format(Analyzer.analysis_name, len(filenames)))

        for filename in filenames:
            logger.info('  Running {} on {}'.format(Analyzer.analysis_name, filename))
            analyzer = Analyzer(*analyzer_args, filename=filename)
            analyzer.set_config(analyzer_config)

            if not analyzer.already_analyzed() or analyzer.force or self.force:
                analyzer.load()
                analyzer.run()
                analyzer.save()
            else:
                logger.info('  Analysis already run')
