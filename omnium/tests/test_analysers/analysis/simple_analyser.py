from omnium.analyser import Analyser
from .analysis_settings import analysis_settings


class SimpleAnalyser(Analyser):
    analysis_name = 'simple_analysis'
    single_file = True
    input_dir = '/a/dir'
    input_filename = 'a.file'
    output_dir = '/a/dir'
    output_filename = 'an.output.file'
    settings = analysis_settings

    def load(self):
        pass

    def run(self):
        pass

    def save(self, state, suite):
        pass
