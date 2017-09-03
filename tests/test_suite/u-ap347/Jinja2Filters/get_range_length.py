#!/usr/bin/env python
import jinja2.filters

@jinja2.filters.contextfilter
def get_range_length(context, range_str):
    """Should be given a range_str like '<start_index>:<end_index', e.g. '1:4'

    returns a string: e.g. 3
    """
    rargs = [int(s) for s in range_str.split(':')]
    return str(len(range(*rargs)))
