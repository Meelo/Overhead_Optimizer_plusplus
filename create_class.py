#!/usr/bin/env python
# -*- coding: utf-8 -*-

from optparse import OptionParser
import os.path
import re


class OverheadOptimizerException(Exception):
    pass


class ClassTemplateProcessor(object):
    def __init__(self):
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

    def process_variable(self, variable_name):
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

    def set_config(self, config):
        self.config = config


class OverheadOptimizerConfig(object):
    def __init__(self):
        self.init_values()

    def set_md5len(self, value):
        try:
            value = int(value)
            if 1 <= value <= 32:
                self.values['md5len'] = value
                return True
        except:
            pass
        return False

    def set_guardstyle(self, value):
        if value in ('underscore', 'nounderscore'):
            self.values['guardstyle'] = value
            return True
        return False

    def set_guardformat(self, value):
        self.values['guardformat'] = value
        return True

    def set_project(self, value):
        self.values['project'] = value
        return True

    def set_projectroot(self, value):
        self.values['projectroot'] = value
        return True

    def set_headerfolder(self, value):
        self.values['headerfolder'] = value
        return True

    def set_sourcefolder(self, value):
        self.values['sourcefolder'] = value
        return True

    def set_defaultnamespace(self, value):
        self.values['defaultnamespace'] = value
        return True

    def set_indent(self, value):
        self.values['indent'] = value.strip("'").strip('"').replace('\\t', '\t')
        return True

    def get(self, variable_name):
        return self.values[variable_name]

    def init_values(self):
        self.values = {}
        self.set_md5len(32)
        self.set_guardstyle('underscore')
        self.set_guardformat('_$PROJECT_$FILENAME_')
        self.set_project('')
        self.set_projectroot('.')
        self.set_headerfolder('include')
        self.set_sourcefolder('src')
        self.set_defaultnamespace('')
        self.set_indent('    ')

    def parse_config_file(self, filename):
        def process_row(row):
            row = row.strip()
            if row.startswith('#') or len(row) == 0:
                return
            try:
                variable, value = row.split('=', 1)
                getattr(self, 'set_' + variable)(value)
                return
            except:
                print 'invalid config file row:', row
                pass

        try:
            for row in open(filename):
                process_row(row)
        except:
            return False
        return True


def create_class(name, namespace=None, baseclass=None, is_interface=False):

    config = OverheadOptimizerConfig()
    config.parse_config_file('config.sample')

    prog_path = os.path.dirname(__file__)
    try:
        h_template_file = os.path.join(prog_path, 'templates', 'class.h.tpl')
        h_template_str = open(h_template_file).read()
    except:
        raise OverheadOptimizerException('Could not open template file ' + \
                                         '"%s"' % h_template_file)
    try:
        c_template_file = os.path.join(prog_path, 'templates', 'class.cpp.tpl')
        c_template_str = open(c_template_file).read()
    except:
        raise OverheadOptimizerException('Could not open template file ' + \
                                         '"%s"' % c_template_file)

    ctp = ClassTemplateProcessor()
    ctp.set_config(config)
    ctp.set_class_name(name)
    ctp.set_baseclass(baseclass)
    if namespace:
        ctp.use_namespaces(namespace.split('::'))
    ctp.is_interface = is_interface

    def process_variable(match):
        return ctp.process_variable(match.group(1))

    class_h = open('%s.h' % name, 'w')
    class_str = re.sub('##([^#]+)#', process_variable, h_template_str)
    class_h.write(class_str)
    class_h.close()

    class_c = open('%s.cpp' % name, 'w')
    class_str = re.sub('##([^#]+)#', process_variable, c_template_str)
    class_c.write(class_str)
    class_c.close()


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
