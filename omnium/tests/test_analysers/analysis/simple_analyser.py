from omnium.analyser import Analyser
from .analysis_settings import analysis_settings


class SimpleAnalyser(Analyser):
    analysis_name = 'simple_analysis'
    single_file = True
    input_dir = ''
    input_filename = ''
    output_dir = ''
    output_filename = ''
    settings = analysis_settings

    def load(self):
        pass

    def run(self):
        pass

    def save(self, state, suite):
        pass
