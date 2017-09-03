import csv

from omnium.analyser import Analyser


class CsvAnalyser(Analyser):
    analysis_name = 'csv_analysis'

    def run_analysis(self):
        self.new_data = []
        for data_line in self.data:
            print(data_line)
            new_data_line = [5 * v for v in map(float, data_line)]
            self.new_data.append(new_data_line)

    def load(self):
        # Intentional override.
        with open(self.filename, 'r') as f:
            reader = csv.reader(f)
            lines = [l for l in reader]
        self.header = lines[0]
        self.data = lines[1:]

    def save(self, state, suite):
        with open(self.filename + '.out', 'wb') as f:
            writer = csv.writer(f, delimiter=',')
            writer.writerow(self.header)
            for data_line in self.new_data:
                writer.writerow(data_line)
