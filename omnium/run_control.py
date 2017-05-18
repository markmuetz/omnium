import os
import sys
from glob import glob
from configparser import ConfigParser

from omnium.analyzers import get_analysis_classes


class RunControl(object):
    def __init__(self):
        self.cylc_control = os.getenv('CYLC_CONTROL') == 'True'

    def run(self):
	dataw_dir, datam_dir, suite = self.read_env()
	data_type, expt = self.read_args()
	self.dataw_dir = dataw_dir
	self.datam_dir = datam_dir
	self.suite = suite
	self.data_type = data_type
	self.expt = expt

	self.run_analysis(dataw_dir, datam_dir, suite, data_type, expt)

    def read_env(self):
	dataw_dir = os.getenv('DATAW')
	datam_dir = os.getenv('DATAM')
	suite = os.getenv('CYLC_SUITE_NAME')

	return dataw_dir, datam_dir, suite

    def read_args(self):
	data_type = sys.argv[1]
	expt = sys.argv[2]
	return data_type, expt

    def read_config(self, config_dir):
	config = ConfigParser()
	with open(os.path.join(config_dir, 'rose-app-run.conf'), 'r') as f:
	    config.read_file(f)
	return config

    def run_analysis(self, config_dir, datam_dir, suite, data_type, expt):
	config = self.read_config(config_dir)
	self.config = config

	settings_sec = '{}_settings'.format(data_type)
	runcontrol_sec = '{}_runcontrol'.format(data_type)

	settings = config[settings_sec]
	runcontrol = config[runcontrol_sec]

	convert = settings['convert_to_nc'] == 'True'
	overwrite = settings['overwrite'] == 'True'
	delete = settings['delete'] == 'True'

	self.analyzers = get_analysis_classes(config_dir)

	if convert:
	    if data_type == 'datam':
		filenames = sorted(glob(os.path.join(datam_dir, 'atmos.???.pp?')))
	    elif data_type == 'dataw':
		# N.B. config_dir is DATAW *for the current task*.
		# Need to work out where the atmos DATAW dir is.
		dataw_dir = os.path.join(os.path.dirname(config_dir), expt + '_atmos')
		filenames = sorted(glob(os.path.join(dataw_dir, 'atmos.pp?')))

	    for filename in filenames:
		try:
		    convert_to_nc(filename, overwrite, delete)
		except:
		    print('Could not convert {}'.format(filename))

	for ordered_analysis, enabled_str in sorted(runcontrol.items()):
	    analysis = ordered_analysis[3:]
	    enabled = enabled_str == 'True'
	    if not enabled:
		continue
	    print('Run analysis: {}'.format(analysis))

	    if config.has_section(analysis):
		analyzer_config = config[analysis]
	    else:
		raise Exception('NO CONFIG FOR ANALYSIS, SKIPPING')

	    if analysis not in self.analyzers:
		raise Exception('COULD NOT FIND ANALYZER: {}'.format(analysis))

	    Analyzer = self.analyzers[analysis]
            print(Analyzer)

	    filename = analyzer_config.pop('filename')
	    if data_type == 'dataw':
		print(filename)

		data_dir = dataw_dir
		results_dir = config_dir
		analyzer = Analyzer(suite, expt, data_type, data_dir, results_dir, filename)
		analyzer.set_config(analyzer_config)
		if not analyzer.already_analyzed() or analyzer.force:
		    analyzer.load()
		    analyzer.run()
		    analyzer.save()
		else:
		    print('analysis already run')
	    elif data_type == 'datam':
		# filename can be a glob.
                print(datam_dir)
                print(filename)
		filenames = Analyzer.get_files(datam_dir, filename)
		for actual_filename in filenames:
		    print(actual_filename)
		    results_dir = datam_dir
		    analyzer = Analyzer(suite, expt, data_type, datam_dir, results_dir, actual_filename)
		    analyzer.set_config(analyzer_config)
		    if not analyzer.already_analyzed() or analyzer.force:
			analyzer.load()
			analyzer.run()
			analyzer.save()
		    else:
			print('analysis already run')
	    else:
		raise Exception('Unknown data_type: {}'.format(data_type))

