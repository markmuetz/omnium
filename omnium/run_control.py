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
    def __init__(self, run_type, expts, force=False):
        self.cylc_control = os.getenv('CYLC_CONTROL') == 'True'
        self.run_type = run_type
        if self.run_type == 'suite':
            self.expts = expts
        else:
            assert len(expts) == 1
            self.expts = expts

        self.force = force

        logger.warn('Disabling Python warnings')
        import warnings
        warnings.filterwarnings("ignore")

    def _read_env(self):
        suite_name = os.getenv('CYLC_SUITE_NAME')
        initial_cycle_point = os.getenv('CYLC_SUITE_INITIAL_CYCLE_POINT')
        suite_dir = os.getenv('CYLC_SUITE_RUN_DIR')

        return suite_name, initial_cycle_point, suite_dir

    def _read_config(self, config_dir, config_filename='rose-app-run.conf'):
        config = ConfigParser()
        with open(os.path.join(config_dir, config_filename), 'r') as f:
            config.read_file(f)
        return config

    def setup(self):
        suite = Suite()
        if self.cylc_control:
            # Running through cylc.
            (suite_name, initial_cycle_point, suite_dir) = self._read_env()
            try:
                suite.check_in_suite_dir(suite_dir)
            except OmniumError:
                logger.warn('Not a suite dir: {}'.format(suite_dir))
                return
        else:
            suite = Suite()
            try:
                suite.check_in_suite_dir(os.getcwd())
            except OmniumError:
                logger.warn('Not in suite')
                return

        self.suite = suite
        suite_name = suite.name

        work_dir = os.path.join(self.suite.suite_dir, 'work')
        initial_cycle_point_dir = sorted(glob(os.path.join(work_dir, '*')))[0]
        initial_cycle_point = os.path.basename(initial_cycle_point_dir)
        suite_dir = suite.suite_dir
        self.analyzers_dir = self.suite.omnium_analysis_dir

        self.suite_name = suite_name
        self.suite_dir = suite_dir

        # Reading from this dir means I can't change the conf based on the cycle,
        # Is this a problem?
        conf_dir = os.path.join(self.suite_dir, 'app/omnium')
        self.config = self._read_config(conf_dir, 'rose-app.conf')

        self.atmos_datam_dir = {}
        self.atmos_dataw_dir = {}

        for expt in self.expts:
            self.atmos_datam_dir[expt] = os.path.join(suite_dir, 'share/data/history', expt)
            self.atmos_dataw_dir[expt] = os.path.join(suite_dir, 'work',
                                                      initial_cycle_point, expt + '_atmos')

    def check_setup(self):
        if not os.path.exists(self.analyzers_dir):
            logger.warn('Dir does not exist: {}'.format(self.analyzers_dir))
        for expt in self.expts:
            data_dir = self.atmos_datam_dir[expt]
            if not os.path.exists(data_dir):
                logger.warn('Dir does not exist: {}'.format(data_dir))
            data_dir = self.atmos_dataw_dir[expt]
            if not os.path.exists(data_dir):
                logger.warn('Dir does not exist: {}'.format(data_dir))

    def print_setup(self):
        for attr in ['cylc_control', 'run_type', 'expts', 'suite_name', 'analyzers_dir',
                     'atmos_datam_dir', 'atmos_dataw_dir']:
            print('{}: {}'.format(attr, getattr(self, attr)))

    def run(self):
        self.gen_analysis_workflow()
        self.run_all()

    def convert_all(self, converter_name, filename_globs, overwrite, delete):
        for expt in self.expts:
            if self.run_type == 'cycle':
                data_dir = self.atmos_datam_dir[expt]
            elif self.run_type == 'expt':
                data_dir = self.atmos_dataw_dir[expt]

            filenames = []
            logger.info('Converting files like:')
            for filename_glob in filename_globs:
                logger.info('  ' + filename_glob)
                for filename in sorted(glob(os.path.join(data_dir, filename_glob))):
                    # Make sure that UM has finished writing file.
                    if os.path.exists(filename + '.done'):
                        logger.debug('  Adding: {}'.format(filename))
                        filenames.append(filename)
                    else:
                        logger.warn('  Not finished: {}'.format(filename))

            converter = CONVERTERS[converter_name](overwrite, delete)
            filenames_for_conversion = []
            for filename in filenames:
                # Check that file is not being converted by another process.
                if os.path.exists(filename + '.converting'):
                    logger.warn('  Already being converted: {}'.format(filename))
                else:
                    with open(filename + '.converting', 'w') as f:
                        f.write('Converting with {}\n'.format(converter_name))
                    filenames_for_conversion.append(filename)

            if not filenames:
                logger.warn('No files to convert')

            for filename in filenames_for_conversion:
                try:
                    converter.convert(filename)
                    # N.B. if converter fails, there will be a left over .converting file.
                    # This is intentional: I want to see if this has failed.
                    os.remove(filename + '.converting')
                except OmniumError as oe:
                    logger.error('Could not convert {}'.format(filename))
                    logger.error(oe)

            if not filenames_for_conversion:
                logger.warn('No files not already being converted to convert')

    def gen_analysis_workflow(self):
        self.analysis_workflow = OrderedDict()

        config = self.config
        suite_name = self.suite_name
        run_type = self.run_type
        expts = self.expts

        settings_sec = 'settings_{}'.format(run_type)
        runcontrol_sec = 'runcontrol_{}'.format(run_type)

        settings = config[settings_sec]

        convert = settings.getboolean('convert', False)
        if convert:
            converter_name = settings.get('converter', 'ff2nc')
            overwrite = settings.getboolean('overwrite', False)
            delete = settings.getboolean('delete', False)
            filename_globs = settings['filenames'].split(',')
            self.convert_all(converter_name, filename_globs, overwrite, delete)

        if runcontrol_sec in config:
            runcontrol = config[runcontrol_sec]
        else:
            logger.info('No runcontrol for {}'.format(self.run_type))
            return

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
            for expt in expts:
                logger.debug('Adding analysis, expt: {}, {}'.format(analysis, expt))

                if analyzer_config['data_type'] == 'datam':
                    data_dir = self.atmos_datam_dir[expt]
                    results_dir = self.atmos_datam_dir[expt]
                elif analyzer_config['data_type'] == 'dataw':
                    data_dir = self.atmos_dataw_dir[expt]
                    results_dir = self.atmos_dataw_dir[expt]

                if (analysis, expt) in self.analysis_workflow:
                    raise OmniumError('({}, {}) already in analysis workflow'.format(analysis,
                                                                                     expt))

                analyzer_args = [suite_name, analyzer_config['data_type'],
                                 data_dir, results_dir, expt]
                self.analysis_workflow[(analysis, expt)] = (Analyzer, analyzer_args,
                                                            analyzer_config, filename_glob)

        logger.debug(self.analysis_workflow.keys())

    def run_analysis(self, analysis, expt):
        (Analyzer, analyzer_args,
         analyzer_config, filename_glob) = self.analysis_workflow[(analysis, expt)]
        self._setup_run_analyzer(Analyzer, analyzer_args, analyzer_config, filename_glob)

    def run_all(self):
        for (Analyzer, analyzer_args,
             analyzer_config, filename_glob) in self.analysis_workflow.values():
            self._setup_run_analyzer(Analyzer, analyzer_args, analyzer_config, filename_glob)

    def _setup_run_analyzer(self, Analyzer, analyzer_args, analyzer_config, filename_glob):
        suite_name, data_type, data_dir, results_dir, expt = analyzer_args

        if analyzer_config['data_type'] == 'datam':
            filenames = Analyzer.get_files(data_dir, filename_glob)
        elif analyzer_config['data_type'] == 'dataw':
            filenames = [filename_glob]

        logger.info('Running {} on {} files'.format(Analyzer.analysis_name, len(filenames)))

        if analyzer_config.getboolean('multi_file', False):
            self._run_analyzer(Analyzer, analyzer_args, analyzer_config, filenames=filenames)
        else:
            for filename in filenames:
                self._run_analyzer(Analyzer, analyzer_args, analyzer_config, filename=filename)

    def _run_analyzer(self, Analyzer, analyzer_args, analyzer_config,
                      filename=None, filenames=None):
        logger.info('  Running {} on {}'.format(Analyzer.analysis_name, filename))
        logger.debug('analyzer_args: {}'.format(analyzer_args))
        analyzer = Analyzer(*analyzer_args, filename=filename, filenames=filenames)
        analyzer.set_config(analyzer_config)

        if not analyzer.already_analyzed() or analyzer.force or self.force:
            analyzer.load()
            analyzer.run()
            analyzer.save()
        else:
            logger.info('  Analysis already run')
