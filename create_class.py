#!/usr/bin/env python
# -*- coding: utf-8 -*-

from optparse import OptionParser

def create_class(name, namespace, baseclass, interface):

    # TODO: real action

    print 'Creating class:', name
    if namespace:
        print ' - using namespace:', namespace
    if baseclass:
        print ' - inherited from baseclass:', baseclass
    if interface:
        print ' - is interface'


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
