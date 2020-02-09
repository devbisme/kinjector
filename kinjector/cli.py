# -*- coding: utf-8 -*-

import argparse
import os
import shutil
import sys
import logging
import collections
import json
import yaml
import pcbnew
from .kinjector import *
from .pckg_info import version


def main():
    """Command-line interface."""

    parser = argparse.ArgumentParser(
        description=
        '''Inject/eject JSON/YAML data to/from a KiCad project file.''')

    parser.add_argument('--version',
                        '-v', '-V',
                        action='version',
                        version='kinjector ' + version)

    parser.add_argument(
        '--from_',
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
        metavar='file.[json|yaml|kicad_pcb]',
        help='''Insert values into one or more JSON/YAML/KiCad files.''')

    parser.add_argument('--overwrite',
                        '-w',
                        action='store_true',
                        help='Allow value insertion into an existing file.')

    parser.add_argument('--nobackup',
                        '-nb',
                        action='store_true',
                        help='''Do *not* create backups before modifying files.
            (Default is to make backup files.)''')

    parser.add_argument(
        '--debug',
        '-d',
        nargs='?',
        type=int,
        default=0,
        metavar='LEVEL',
        help='Print debugging info. (Larger LEVEL means more info.)')

    args = parser.parse_args()

    logger = logging.getLogger('kinjector')
    if args.debug is not None:
        log_level = logging.DEBUG + 1 - args.debug
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(log_level)
        logger.addHandler(handler)
        logger.setLevel(log_level)

    if args.from_ is None:
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

    # Combine the input files into a single injection dict.
    injection_dict = {}
    for file in args.from_:
        fp = open(file, 'r')  # Throw exception if file doesn't exist.
        try:
            # Do this if it's a JSON file.
            fp.seek(0)
            file_dict = json.load(fp)
        except Exception:
            try:
                # Do this if it's a YAML file.
                fp.seek(0)
                file_dict = yaml.load(fp, Loader=yaml.Loader)
                if not isinstance(file_dict, collections.Mapping):
                    raise Exception
            except Exception:
                try:
                    # Do this if it's a KiCad board file.
                    fp.close()
                    brd = pcbnew.LoadBoard(file)
                    file_dict = Board().eject(brd)
                except Exception as e:
                    # OK, it's none of those things.
                    print("Hey! I can't handle this input file:", file)
                    raise e
        merge_dicts(injection_dict, file_dict)
        fp.close()

    # Insert the injection dict into each of the output files.
    for file in args.to:
        try:
            fp = open(file, 'r')

            # The file exists and could be opened, now find out what type it is.
            try:
                file_dict = json.load(fp) # Causes exception if not JSON.
                fp.close()
                # Overwrite the JSON file.
                with open(file, 'w') as fp:
                    json.dump(injection_dict, fp, indent=4)
            except Exception:
                try:
                    file_dict = yaml.load(fp, Loader=yaml.Loader) # Exception if not YAML.
                    fp.close()
                    # Overwrite the YAML file.
                    with open(file, 'w') as fp:
                        yaml.safe_dump(injection_dict, fp, default_flow_style=False)
                except Exception:
                    try:
                        fp.close()
                        brd = pcbnew.LoadBoard(file) # Exception if not KiCad board file.
                        # Inject the new values into the board.
                        Board().inject(injection_dict, brd)
                        # Overwrite the KiCad board file.
                        brd.Save(file)
                    except Exception as e:
                        raise e
        except IOError:
            # No existing file, so create a file with the injection dict contents.
            file_ext = str.lower(os.path.splitext(file)[1])
            if file_ext == '.json':
                with open(file,'w') as fp:
                    json.dump(injection_dict, fp, indent=4)
            elif file_ext == '.yaml':
                with open(file,'w') as fp:
                    yaml.safe_dump(injection_dict, fp, default_flow_style=False)
            else:
                Board().inject(injection_dict, brd)
                brd.Save(file)


###############################################################################
# Main entrypoint.
###############################################################################
if __name__ == '__main__':
    main()
