from .analysis_settings import settings
from .csv_analyser import CsvAnalyser
from .simple_analyser import SimpleAnalyser

__version__ = (0, 0, 0, 1)

analysis_settings_filename = 'omnium_output/{version_dir}/settings.json'

analysis_settings = {
    'default': settings,
}

analyser_classes = [CsvAnalyser, SimpleAnalyser]
