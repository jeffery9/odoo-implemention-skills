#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import optparse
import sys
import glob
import logging

# command to use: python3  ~/odoo_module_graph.py stock_barcode  -p .  | dot -Tpng -o ~/odoo15.png

# TODO use the same function provided in openerp.modules
def load_information_from_description_file(module):
    """
    :param module: The name of the module (sale, purchase, ...)
    """
    for filename in ['__manifest__.py', '__openerp__.py', '__terp__.py']:
        description_file = os.path.join(module, filename)
        if os.path.isfile(description_file):
            return eval(open(description_file).read())

    return {}


def get_valid_path(paths, module):
    for path in paths:
        full = os.path.join(path, module)
        if os.path.exists(full):
            return full
    return None


def main(opt, args):
    modules = []
    if not opt.path:
        opt.path = ["."]

    if not args:
        for path in opt.path:
            modules += map(
                os.path.dirname,
                glob.glob(os.path.join(path, '*', '__manifest__.py')))
            modules += map(
                os.path.dirname,
                glob.glob(os.path.join(path, '*', '__openerp__.py')))
            modules += map(os.path.dirname,
                           glob.glob(os.path.join(path, '*', '__terp__.py')))
    else:
        for module in args:
            for addons in os.listdir(opt.path[0]):
                if module in addons:
                    valid_path = get_valid_path(opt.path, addons)
                    if valid_path:
                        modules.append(valid_path)

    all_modules = set(map(os.path.basename, modules))

    graph = []

    def put_graph(k):
        if k not in graph:
            graph.append(k)

    line = 'digraph G {'
    graph.append(line)
    while len(modules):
        f = modules.pop(0)
        module_name = os.path.basename(f)
        all_modules.add(module_name)
        info = load_information_from_description_file(f)
        if info.get('installable', True):
            if info.get('license', '') == 'OEEL-1':
                node = '\t%s [color=darkmagenta,fontweight="bold"]' % (module_name)
                put_graph(node)

            for name in info.get('depends', []):
                valid_path = get_valid_path(opt.path, name)
                if name not in all_modules:
                    if valid_path:
                        modules.append(valid_path)
                    else:
                        all_modules.add(name)
                        line = '\t%s [color=red]' % (name)
                        put_graph(line)

                line = '\t%s -> %s;' % (module_name, name)
                put_graph(line)

    graph.append('}')

    return graph


if __name__ == '__main__':
    parser = optparse.OptionParser(
        usage="%prog [options] [module1 [module2 ...]]")
    parser.add_option("-p",
                      "--addons-path",
                      dest="path",
                      help="addons directory",
                      action="append")
    (opt, args) = parser.parse_args()
    if not opt.path:
        parser.print_help()

    else:
        graph = main(opt, args)
        for line in graph:
            print(line)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: