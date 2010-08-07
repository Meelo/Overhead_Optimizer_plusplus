#!/usr/bin/env python
# -*- coding: utf-8 -*-

from optparse import OptionParser
import os.path
import re


class OverheadOptimizerException(Exception):
    pass


class ClassTemplateProcessor(object):
    def __init__(self, template_str):
        self.template_str = template_str
        self.namespaces = []

    def use_namespaces(self, namespaces):
        self.namespaces = namespaces

    def namespaces_begin_str(self):
        def ns_begin(ns_name):
            return 'namespace %s\n{' % ns_name
        return '\n'.join(ns_begin(ns) for ns in self.namespaces)

    def namespaces_end_str(self):
        def ns_end(ns_name):
            return '} // namespace %s' % ns_name
        return '\n'.join(ns_end(ns) for ns in reversed(self.namespaces))

    def process_variable(self, variable_match):
        variable_name = variable_match.group(1)

        if variable_name == 'NAMESPACES_BEG':
            return self.namespaces_begin_str()
        if variable_name == 'NAMESPACES_END':
            return self.namespaces_end_str()
        if variable_name == 'CLASS_NAME':
            return self.class_name
        if variable_name == 'INHERITANCE':
            return ': public %s' % self.baseclass if self.baseclass else ''

        return '[%s notImplemented]' % variable_name

    def set_baseclass(self, baseclass):
        self.baseclass = baseclass

    def set_class_name(self, class_name):
        self.class_name = class_name


def create_class(name, namespace=None, baseclass=None, is_interface=False):

    prog_path = os.path.dirname(__file__)
    try:
        template_file = os.path.join(prog_path, 'templates', 'class.h.tpl')
        template_str = open(template_file).read()
    except:
        raise OverheadOptimizerException('Could not open template file ' + \
                                         '"%s"' % template_file)

    ctp = ClassTemplateProcessor(template_str)
    ctp.set_class_name(name)
    ctp.set_baseclass(baseclass)
    if namespace:
        ctp.use_namespaces(namespace.split('::'))
    ctp.is_interface = is_interface

    class_cpp = open('%s.cpp' % name, 'w')
    class_str = re.sub('##([^#]+)#', ctp.process_variable, template_str)
    class_cpp.write(class_str)
    class_cpp.close()


if __name__ == '__main__':
    usage = 'usage: %prog class_name [options]'
    parser = OptionParser(usage=usage)
    parser.add_option('-n', '--namespace', dest='namespace',
                      help='place the new class inside NAMESPACE',
                      metavar='NAMESPACE')
    parser.add_option('-I', '--interface', dest='interface',
                      help='create an interface', action='store_true',
                      default=False)
    parser.add_option('-b', '--baseclass', dest='baseclass',
                      help='inherit new class from BASECLASS',
                      metavar='BASECLASS')
    (options, args) = parser.parse_args()

    # expect class name as first and only argument
    if len(args) != 1:
        print 'Error: invalid arguments'
        parser.print_help()
        raise SystemExit

    class_name = args[0]
    create_class(class_name, options.namespace, options.baseclass,
                 options.interface)
