import csv

from omnium.analyser import Analyser


class CsvAnalyser(Analyser):
    analysis_name = 'csv_analysis'

    def run_analysis(self):
        for data_line in self.data:
            print(data_line)

    def load(self):
        # Intentional override.
        with open(self.filename, 'r') as f:
            reader = csv.reader(f)
            lines = [l for l in reader]
        self.header = lines[0]
        self.data = lines[1:]
