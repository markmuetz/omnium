import iris

def domain_mean(cube):
    return cube.collapsed(['grid_latitude', 'grid_longitude'], iris.analysis.MEAN)

def vertical_profile(cube):
    return cube.collapsed(['grid_latitude', 'grid_longitude'], iris.analysis.MEAN)

