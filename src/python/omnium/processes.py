import iris

def convert_pp_to_nc(args, config, to_node):
    assert(len(to_node.from_nodes) == 1)
    from_node = to_node.from_nodes[0]

    print('Convert {} to {}'.format(from_node, to_node))
    cubes = iris.load(from_node.filename)
    if not len(cubes):
        print('Cubes is empty')
        return
    iris.save(cubes, to_node.filename)

    with open(to_node.filename + '.done', 'w') as f:
        f.write('{}'.format(cubes))
    assert(to_node.exists())


def domain_mean(args, config, to_node):
    results = []
    for from_node in to_node.from_nodes:
        cubes = iris.load(from_node.filename)
        for cube in cubes:
            cube_stash = cube.attributes['STASH']
            section, item = cube_stash.section, cube_stash.item
            if section == to_node.section and item == to_node.item:
                break
        result = cube.collapsed(['grid_latitude', 'grid_longitude'], 
                                iris.analysis.MEAN)
        results.append(result)

    results_cube = iris.cube.CubeList(results).concatenate_cube()
    iris.save(results_cube, to_node.filename)

    with open(to_node.filename + '.done', 'w') as f:
        f.write('{}\n'.format(results_cube))
    assert(to_node.exists())
