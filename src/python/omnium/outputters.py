from os import path
import pylab as plt

def multi_timeseries(timeseries_list, filename):
    plt.ion()
    f, axes = plt.subplots(1, len(timeseries_list))
    f.canvas.set_window_title('timeseries') 
    for i, (name, timeseries) in enumerate(timeseries_list):
	name = timeseries.name()
	times = timeseries.coords()[0].points.copy()
	times -= times[0]

        axes[i].plot(times / 24, timeseries.data)
	axes[i].set_xlabel('time (days)')
	axes[i].set_ylabel(timeseries.units)
        axes[i].set_title(name)

    plt.savefig(filename)


def vertical_profiles_first_last(vp_list, filename):
    plt.ion()
    plt.figure('vertical_profiles')
    vp = vp_list[0][1]
    plt.plot(vp.data[0], vp.aux_coords[4].points)
    plt.plot(vp.data[-1], vp.aux_coords[4].points)
    plt.savefig(filename)
