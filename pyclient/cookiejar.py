#!/usr/bin/env python3

# Copyright 2018 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ------------------------------------------------------------------------------
'''
Command line interface for cookiejar TF.
Parses command line arguments and passes to the CookieJarClient class
to process.
'''

import argparse
import logging
import os
import sys
import traceback

from colorlog import ColoredFormatter
from cookiejar_client import CookieJarClient

KEY_NAME = 'mycookiejar'

# hard-coded for simplicity (otherwise get the URL from the args in main):
#DEFAULT_URL = 'http://localhost:8008'
# For Docker:
DEFAULT_URL = 'http://rest-api:8008'

def create_console_handler(verbose_level):
    '''Setup console logging.'''
    del verbose_level # unused
    clog = logging.StreamHandler()
    formatter = ColoredFormatter(
        "%(log_color)s[%(asctime)s %(levelname)-8s%(module)s]%(reset)s "
        "%(white)s%(message)s",
        datefmt="%H:%M:%S",
        reset=True,
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red',
        })

    clog.setFormatter(formatter)
    clog.setLevel(logging.DEBUG)
    return clog

def setup_loggers(verbose_level):
    '''Setup logging.'''
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(create_console_handler(verbose_level))

def create_parser(prog_name):
    '''Create the command line argument parser for the cookiejar CLI.'''
    parent_parser = argparse.ArgumentParser(prog=prog_name, add_help=False)

    parser = argparse.ArgumentParser(
        description='Provides subcommands to manage your simple cookie baker',
        parents=[parent_parser])

    subparsers = parser.add_subparsers(title='subcommands', dest='command')
    subparsers.required = True

    bake_subparser = subparsers.add_parser('bake',
                                           help='bake some cookies',
                                           parents=[parent_parser])
    bake_subparser.add_argument('amount',
                                type=int,
                                help='the number of cookies to bake')
    eat_subparser = subparsers.add_parser('eat',
                                          help='eat some cookies',
                                          parents=[parent_parser])
    eat_subparser.add_argument('amount',
                               type=int,
                               help='the number of cookies to eat')
    subparsers.add_parser('count',
                          help='show number of cookies in ' +
                          'the cookie jar',
                          parents=[parent_parser])
						  
    clear_subparser = subparsers.add_parser('clear',
                                           help='empties cookie jar',
                                           parents=[parent_parser])					  
						  
    return parser

def _get_private_keyfile(key_name):
    '''Get the private key for key_name.'''
    home = os.path.expanduser("~")
    key_dir = os.path.join(home, ".sawtooth", "keys")
    return '{}/{}.priv'.format(key_dir, key_name)

def do_bake(args):
    '''Subcommand to bake cookies.  Calls client class to do the baking.'''
    privkeyfile = _get_private_keyfile(KEY_NAME)
    client = CookieJarClient(base_url=DEFAULT_URL, key_file=privkeyfile)
    response = client.bake(args.amount)
    print("Bake Response: {}".format(response))

def do_eat(args):
    '''Subcommand to eat cookies.  Calls client class to do the eating.'''
    privkeyfile = _get_private_keyfile(KEY_NAME)
    client = CookieJarClient(base_url=DEFAULT_URL, key_file=privkeyfile)
    response = client.eat(args.amount)
    print("Eat Response: {}".format(response))

def do_count():
    '''Subcommand to count cookies.  Calls client class to do the counting.'''
    privkeyfile = _get_private_keyfile(KEY_NAME)
    client = CookieJarClient(base_url=DEFAULT_URL, key_file=privkeyfile)
    data = client.count()
    if data is not None:
        print("\nThe cookie jar has {} cookies.\n".format(data.decode()))
    else:
        raise Exception("Cookie jar data not found")
		
def do_clear():
    '''Subcommand to empty cookie jar. Calls client class to do the clearing.'''
    privkeyfile = _get_private_keyfile(KEY_NAME)
    client = CookieJarClient(base_url=DEFAULT_URL, key_file=privkeyfile)
    response = client.clear()
    print("Clear Response: {}".format(response))

def main(prog_name=os.path.basename(sys.argv[0]), args=None):
    '''Entry point function for the client CLI.'''
    try:
        if args is None:
            args = sys.argv[1:]
        parser = create_parser(prog_name)
        args = parser.parse_args(args)
        verbose_level = 0
        setup_loggers(verbose_level=verbose_level)

        # Get the commands from cli args and call corresponding handlers
        if args.command == 'bake':
            do_bake(args)
        elif args.command == 'eat':
            do_eat(args)
        elif args.command == 'count':
            do_count()
        elif args.command == 'clear':
            do_clear()	
        else:
            raise Exception("Invalid command: {}".format(args.command))

    except KeyboardInterrupt:
        pass
    except SystemExit as err:
        raise err
    except BaseException as err:
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
