# -*- coding: utf-8 -*-

import argparse
import os
import shutil
import sys
import logging
from .kinjector import *


def main():
    """Command-line interface."""

    parser = argparse.ArgumentParser(
        description=
        '''Inject/eject JSON/YAML data to/from a KiCad project file.''')

    parser.add_argument('--version',
                        '-v',
                        action='version',
                        version='kinjector ' + version)

    parser.add_argument(
        '--from',
        '-f',
        nargs='+',
        type=str,
        metavar='file.[json|yaml|kicad_pcb]',
        help='''Extract values from one or more JSON/YAML/KiCad files.''')

    parser.add_argument(
        '--to',
        '-t',
        nargs='+',
        type=str,
        metavar='file.[kicad_pcb|yaml|json]',
        help='''Insert values into one or more KiCad/YAML/JSON files.''')

    parser.add_argument('--overwrite',
                        '-w',
                        action='store_true',
                        help='Allow value insertion into an existing file.')

    parser.add_argument('--nobackup',
                        '-nb',
                        action='store_true',
                        help='''Do *not* create backups before modifying files.
            (Default is to make backup files.)''')

    # parser.add_argument(
        # '--debug',
        # '-d',
        # nargs='?',
        # type=int,
        # default=0,
        # metavar='LEVEL',
        # help='Print debugging info. (Larger LEVEL means more info.)')

    args = parser.parse_args()

    logger = logging.getLogger('kinjector')
    if args.debug is not None:
        log_level = logging.DEBUG + 1 - args.debug
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(log_level)
        logger.addHandler(handler)
        logger.setLevel(log_level)

    if args.from is None:
        logger.critical('Hey! Give me some files to extract from!')
        sys.exit(2)

    if args.to is None:
        print('Hey! I need some files where I can insert values!')
        sys.exit(1)

    for file in args.to:
        if os.path.isfile(file):
            if not args.overwrite and args.nobackup:
                logger.critical(
                    '''File {} already exists! Use the --overwrite option to
                    allow modifications to it or allow backups.'''.format(
                        file))
                sys.exit(1)
            if not args.nobackup:
                # Create a backup file.
                index = 1  # Start with this backup file suffix.
                while True:
                    backup_file = file + '.{}.bak'.format(index, file)
                    if not os.path.isfile(backup_file):
                        # Found an unused backup file name, so make backup.
                        shutil.copy(file, backup_file)
                        break  # Backup done, so break out of loop.
                    index += 1  # Else keep looking for an unused backup file name.

    kinjector(extract_filenames=args.extract,
              insert_filenames=args.insert,
              inc_field_names=inc_fields,
              exc_field_names=exc_fields)


###############################################################################
# Main entrypoint.
###############################################################################
if __name__ == '__main__':
    main()
