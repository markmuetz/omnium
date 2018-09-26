import os
from omnium.analysis import AnalysisPkgs
from omnium.setup_logging import setup_logger, add_file_logging
from omnium.suite import Suite
from omnium.run_control import RunControl


def run_local_analyser(analysis_pkg_name, analyser_cls, run_type, expts,
                       force=False,
                       debug=False):

    logger = setup_logger(debug, True, True)
    logger.info('Running local analyser: {}'.format(analyser_cls))
    suite = Suite(os.getcwd())

    analysis_pkgs = AnalysisPkgs([analysis_pkg_name], suite)
    analysis_pkg = analysis_pkgs[analysis_pkg_name]

    analysis_pkg[analyser_cls.analysis_name] = analyser_cls
    analysis_pkgs._cls_to_pkg[analyser_cls] = analysis_pkg
    analysis_pkgs.analyser_classes[analyser_cls.analysis_name] = analyser_cls

    suite.set_analysis_pkgs(analysis_pkgs)

    run_control = RunControl(suite, run_type, expts, 'default', force=force)
    run_control._analysis_workflow[analyser_cls.analysis_name] = (analyser_cls.analysis_name,
                                                                  analyser_cls,
                                                                  True)

    run_control.gen_tasks()
    run_control.run_all()
