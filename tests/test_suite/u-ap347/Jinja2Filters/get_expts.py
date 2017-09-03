#!/usr/bin/env python
import jinja2.filters

@jinja2.filters.contextfilter
def get_expts(context, expts):
    """Takes an expts list and returns a space separated list of expts."""
    return '"' + ' '.join([expt['name'] for expt in expts]) + '"'

