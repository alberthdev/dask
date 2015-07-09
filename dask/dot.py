from __future__ import absolute_import, division, print_function

import networkx as nx
from dask.core import istask, get_dependencies


def make_hashable(x):
    try:
        hash(x)
        assert len(str(x)) < 100
        return x
    except:
        return hash(str(x))


def lower(func):
    while hasattr(func, 'func'):
        func = func.func
    return func

def name(func):
    try:
        return lower(func).__name__
    except AttributeError:
        return 'func'


def to_networkx(d, data_attributes=None, function_attributes=None):
    if data_attributes is None:
        data_attributes = dict()
    if function_attributes is None:
        function_attributes = dict()

    g = nx.DiGraph()

    for k, v in sorted(d.items(), key=lambda x: x[0]):
        g.add_node(k, shape='box', **data_attributes.get(k, dict()))
        if istask(v):
            func, args = v[0], v[1:]
            func_node = make_hashable((v, 'function'))
            g.add_node(func_node,
                       shape='circle',
                       label=name(func),
                       **function_attributes.get(k, dict()))
            g.add_edge(func_node, k)
            for dep in sorted(get_dependencies(d, k)):
                arg2 = make_hashable(dep)
                g.add_node(arg2,
                           label=str(dep),
                           shape='box',
                           **data_attributes.get(dep, dict()))
                g.add_edge(arg2, func_node)
        else:
            v_hash = make_hashable(v)
            if v_hash not in d:
                g.add_node(k, label='%s=%s' % (k, v), **data_attributes.get(k, dict()))
            else:  # alias situation
                g.add_edge(v_hash, k)

    return g


def write_networkx_to_dot(dg, filename='mydask'):
    import os
    try:
        p = nx.to_pydot(dg)
    except AttributeError:
        raise ImportError("Can not find pydot module. Please install.\n"
                          "    pip install pydot")
    p.set_rankdir('BT')
    with open(filename + '.dot', 'w') as f:
        f.write(p.to_string())

    os.system('dot -Tpdf %s.dot -o %s.pdf' % (filename, filename))
    os.system('dot -Tpng %s.dot -o %s.png' % (filename, filename))
    print("Writing graph to %s.pdf" % filename)


def dot_graph(d, filename='mydask', **kwargs):
    dg = to_networkx(d, **kwargs)
    write_networkx_to_dot(dg, filename=filename)


if __name__ == '__main__':
    def add(x, y):
        return x + y
    def inc(x):
        return x + 1

    dsk = {'x': 1, 'y': (inc, 'x'),
           'a': 2, 'b': (inc, 'a'),
           'z': (add, 'y', 'b')}

    dot_graph(dsk)
