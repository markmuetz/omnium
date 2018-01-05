from omnium.analyser import Analyser


class SimpleAnalyser(Analyser):
    analysis_name = 'simple_analysis'
    single_file = True

    def run_analysis(self):
        pass
