"""Run processing"""
import os

import iris

from omnium.umo import UMO
import omnium.processes
from omnium.results import ResultsManager

ARGS = []

def main(args, config):
    settings = config.settings
    umo = UMO(config)
    rm = ResultsManager(config)

    # TODO: it is inefficient to loop over cubes like this.
    for output_var in config.output_vars.options():
        results = []
        sec = getattr(config, output_var)
        filenames = umo.filenames_by_stream[sec.stream]
        args = [sec.process, sec.section, sec.item]
        args.extend(filenames)

        if rm.has(*args):
            print('Loading previously saved result')
            results_cube = rm.load(*args)
            continue

        process = getattr(omnium.processes, sec.process)

        for filename in filenames:
            umo.load_cubes(filename)
            umo.set_cube(sec.stream, sec.section, sec.item)
            result = process(umo.cube)
            results.append(result)

        results_cube = iris.cube.CubeList(results).concatenate_cube()

        rm.save(results_cube, *args)
