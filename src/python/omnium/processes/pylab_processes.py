import subprocess as sp

import pylab as plt
import iris

from stash import stash
from omnium.processes import Process

class PylabProcess(Process):
    def save(self):
        super(PylabProcess, self).save()
        filename = self.node.filename(self.config)
        plt.savefig(filename)
        self.saved = True

    def view(self):
        assert(self.node.status == 'done')
        sp.call(['eog', self.node.filename(self.config)])


class PlotMultiTimeseries(PylabProcess):
    name = 'plot_multi_timeseries'
    out_ext = 'png'

    def load_upstream(self):
        super(PlotMultiTimeseries, self).load_upstream()
        filenames = [n.filename(self.config) for n in self.node.from_nodes]
        all_timeseries = iris.load_upstream(filenames)
        self.data = all_timeseries
        return all_timeseries

    def run(self):
        super(PlotMultiTimeseries, self).run()
	all_timeseries = self.data
        fig, axes = plt.subplots(1, len(all_timeseries))
        if len(all_timeseries) == 1:
            axes = [axes]
        fig.canvas.set_window_title('timeseries') 
        for i, timeseries in enumerate(all_timeseries):
            times = timeseries.coords()[0].points.copy()
            times -= times[0]

            axes[i].plot(times / 24, timeseries.data)
            axes[i].set_xlabel('time (days)')
            axes[i].set_ylabel(timeseries.units)
            axes[i].set_title(timeseries.name())
        self.processed_data = fig


class PlotLastProfile(PylabProcess):
    name = 'plot_last_profile'
    out_ext = 'png'

    def load_upstream(self):
        super(PlotLastProfile, self).load_upstream()
        filenames = [n.filename(self.config) for n in self.node.from_nodes]
        profiles = iris.load_upstream(filenames)
        self.data = profiles

    def run(self):
        super(PlotLastProfile, self).run()
        profiles = self.data

        fig = plt.figure()
        fig.canvas.set_window_title('profile') 
        for i, profile in enumerate(profiles):
            last_profile = profile[-1]
            stash.rename_unknown_cube(last_profile)
            plt.plot(last_profile.data, last_profile.coord('level_height').points, label=last_profile.name())

        plt.legend()
        self.processed_data = fig
