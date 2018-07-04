from .csv_analyser import CsvAnalyser
from .simple_analyser import SimpleAnalyser
from .analysis_settings import settings

analysis_settings = {
    'default': settings,
}


analysis_classes = [CsvAnalyser, SimpleAnalyser]
