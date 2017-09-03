#!/usr/bin/env python

import jinja2.filters

@jinja2.filters.contextfilter

def get_variable(context, variable_name):
    """Gets the value of a variable.
        
       Arguments:
         variable_name -- the name of the variable whose value is 
                          desired
       Returns:
         The value of variable_name if it exists in the context, 
         else None
    """
    if variable_name in context:
        return context[variable_name]
    else:
        return None

