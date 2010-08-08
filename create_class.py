#!/usr/bin/env python
# -*- coding: utf-8 -*-

from optparse import OptionParser
import os
import os.path
import re
import time
import sys
from hashlib import md5


class OverheadOptimizerException(Exception):
    pass


class ClassTemplateProcessor(object):
    def __init__(self, filename_base):
        self.namespaces = []
        self.filename_base = filename_base # without .h or .cpp

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

    def guard_str(self):
        to_hash = self.config.get('project') + self.class_name + str(time.time)
        md5_hash = md5(to_hash).hexdigest()[:self.config.get('md5len')]
        s = self.config.get('guardformat')
        s = s.replace('$PROJECT', self.config.get('project'))
        s = s.replace('$FILENAME', self.class_name + '.h')
        s = s.replace('$CLASS', self.class_name)
        s = s.replace('$PATH', self.config.get('headerfolder'))
        s = s.replace('$MD5', md5_hash)
        s = re.sub('[^a-zA-Z0-9_]', '_', s)
        s = re.sub('_+', '_', s)
        s = s.upper()
        return s

    def process_variable(self, variable_name):
        if variable_name == 'NAMESPACES_BEG':
            return self.namespaces_begin_str()
        if variable_name == 'NAMESPACES_END':
            return self.namespaces_end_str()
        if variable_name == 'CLASS_NAME':
            return self.class_name
        if variable_name == 'CLASS_FILENAME':
            return self.filename_base
        if variable_name == 'INHERITANCE':
            return ': public %s' % self.baseclass if self.baseclass else ''
        if variable_name == 'GUARD':
            return self.guard_str()
        if variable_name == 'INDENT':
            return self.config.get('indent')

        return '[%s not implemented]' % variable_name

    def set_baseclass(self, baseclass):
        self.baseclass = baseclass

    def set_class_name(self, class_name):
        self.class_name = class_name

    def set_config(self, config):
        self.config = config


class OverheadOptimizerConfig(object):
    def __init__(self):
        self.init_values()

    def setvar_md5len(self, value):
        try:
            value = int(value)
            if 1 <= value <= 32:
                self.values['md5len'] = value
                return True
        except:
            pass
        return False

    def setvar_guardstyle(self, value):
        if value in ('underscore', 'nounderscore'):
            self.values['guardstyle'] = value
            return True
        return False

    def setvar_guardformat(self, value):
        self.values['guardformat'] = value
        return True

    def setvar_project(self, value):
        self.values['project'] = value
        return True

    def setvar_projectroot(self, value):
        self.values['projectroot'] = value
        return True

    def setvar_filenameformat(self, value):
        if value in ('classname', 'lowercase', 'lower_case'):
            self.values['filenameformat'] = value
            return True
        return False

    def setvar_headerfolder(self, value):
        self.values['headerfolder'] = value
        return True

    def setvar_sourcefolder(self, value):
        self.values['sourcefolder'] = value
        return True

    def setvar_defaultnamespace(self, value):
        self.values['defaultnamespace'] = value
        return True

    def setvar_indent(self, value):
        self.values['indent'] = value.strip("'").strip('"').replace('\\t', '\t')
        return True

    def get(self, variable_name):
        return self.values[variable_name]

    def init_values(self):
        self.values = {}
        self.setvar_md5len(32)
        self.setvar_filenameformat('classname')
        self.setvar_guardstyle('underscore')
        self.setvar_guardformat('_$PROJECT_$FILENAME_')
        self.setvar_project('')
        self.setvar_projectroot('.')
        self.setvar_headerfolder('include')
        self.setvar_sourcefolder('src')
        self.setvar_defaultnamespace('')
        self.setvar_indent('    ')

    def parse_config_file(self, filename, reset_config=True):
        if reset_config:
            self.init_values()

        def process_row(row):
            row = row.strip()
            if row.startswith('#') or len(row) == 0:
                return
            try:
                variable, value = row.split('=', 1)
                if not getattr(self, 'setvar_' + variable)(value):
                    raise OverheadOptimizerException()
                return
            except:
                print 'Warning: ignored invalid config file row:', row
                pass

        try:
            for row in open(filename):
                process_row(row)
        except:
            return False
        return True


class ClassCreator(object):
    def __init__(self, class_name):
        self.class_name = class_name
        self.namespaces = []
        self.is_interface = False
        self.config = None
        self.overwrite = False

    def add_namespace(self, namespace):
        self.namespaces.append(namespace)

    def use_config(self, config):
        self.config = config

    def use_dirs(self, cwd, script_dir):
        self.cwd = cwd
        self.script_dir = script_dir

    def create_file(self, target_filename, tpl_filename, template_processor):
        # read template file
        try:
            template_str = open(tpl_filename).read()
        except:
            print "Error: Could not open template file '%s'" % tpl_filename

        if os.path.isfile(target_filename) and self.overwrite == False:
            q = "Warning! Target '%s' exists. Overwrite? (Y)es/(N)o?" % \
                target_filename
            while True:
                res = raw_input(q + ' ')[:1].lower()
                if res == 'y':
                    break
                elif res == 'n':
                    print 'Write cancelled'
                    return

        def process_variable(match):
            return template_processor.process_variable(match.group(1))

        f = open(target_filename, 'w')
        out_str = re.sub('##([^#]+)#', process_variable, template_str)
        f.write(out_str)
        f.close()

    def init_tpl_processor(self):
        ctp = ClassTemplateProcessor(self.format_filename())
        ctp.set_config(self.config)
        ctp.set_class_name(self.class_name)
        ctp.set_baseclass(self.baseclass)
        ctp.use_namespaces(self.namespaces)
        ctp.is_interface = self.is_interface
        return ctp

    def format_filename(self):
        if self.config.get('filenameformat') == 'lowercase':
            return self.class_name.lower()
        if self.config.get('filenameformat') == 'lower_case':
            res = re.sub('([A-Z])', r'_\1', self.class_name).lower()
            return res.lstrip('_')
        return self.class_name

    def init_header_file_name(self):
        """Return header file name. Create directories if needed."""

        path = os.path.abspath(self.config.get('projectroot'))
        if not os.path.isdir(path):
            os.mkdir(path, 0755)

        path = os.path.join(path, self.config.get('headerfolder'))
        if not os.path.isdir(path):
            os.mkdir(path, 0755)

        return os.path.join(path, self.format_filename() + '.h')

    def init_class_file_name(self):
        """Return header file name. Create directories if needed."""

        path = os.path.abspath(self.config.get('projectroot'))
        if not os.path.isdir(path):
            os.mkdir(path, 0755)
        path = os.path.join(path, self.config.get('sourcefolder'))
        if not os.path.isdir(path):
            os.mkdir(path, 0755)

        return os.path.join(path, self.format_filename() + '.cpp')

    def create_class_files(self):
        if not self.config:
            # use defaults
            self.config = OverheadOptimizerConfig()

        tp = self.init_tpl_processor()

        tpl_dir = os.path.join(self.script_dir, 'templates')
        tpl_files = ('class.h.tpl', 'class.cpp.tpl')
        target_files = (self.init_header_file_name(), \
                        self.init_class_file_name())

        for target, tpl_file in zip(target_files, tpl_files):
            tpl_filepath = os.path.join(tpl_dir, tpl_file)
            self.create_file(target, tpl_filepath, tp)

def parse_arguments():
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
    parser.add_option('-c', '--config_file', dest='config_file',
                      help='read config from CONFIG_FILE',
                      metavar='CONFIG_FILE')
    parser.add_option('-O', '--overwrite', dest='overwrite',
                      help='overwrite existing target files, otherwise ask',
                      action='store_true', default=False)
    return parser.parse_args()

def init_config(cwd, script_dir, config_file=None):
    default_filename = 'config'
    locations = [os.path.join(x, default_filename) for x in (cwd, script_dir)]
    if config_file:
        locations.insert(0, os.path.abspath(config_file))

    config = OverheadOptimizerConfig()
    for filename in locations:
        if not os.path.isfile(filename):
            continue
        if config.parse_config_file(filename):
            print "Using config file '%s'" % filename
            return config

    print "Error: Unable to find or open config file. Expecting " + \
          "'%s' in current working dir, " % default_filename + \
          "in script directory ('%s') " % script_dir + \
          "or filename given with -c option."
    raise OverheadOptimizerException()

def get_namespaces(config, options_namespaces):
    namespaces = []
    if config.get('defaultnamespace'):
        namespaces.extend(config.get('defaultnamespace').split('::'))
    if options_namespaces:
        namespaces.extend(options_namespaces.split('::'))
    return namespaces

def main():
    options, args = parse_arguments()
    cwd = os.getcwd()
    script_dir = os.path.abspath(os.path.dirname(__file__))

    config = init_config(cwd, script_dir, options.config_file)

    # expect class name as only non-option argument
    if len(args) != 1:
        print 'Error: invalid arguments'
        parser.print_help()
        raise SystemExit

    class_name = args[0]
    cc = ClassCreator(class_name)
    cc.use_config(config)

    namespaces = get_namespaces(config, options.namespace)
    for ns in namespaces:
        cc.add_namespace(ns)

    cc.is_interface = options.interface
    cc.overwrite = options.overwrite
    cc.baseclass = options.baseclass
    cc.use_dirs(cwd, script_dir)

    cc.create_class_files()

if __name__ == '__main__':
    try:
        main()
    except OverheadOptimizerException:
        sys.exit(-1)
