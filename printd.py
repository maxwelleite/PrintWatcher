#!/usr/bin/env python3

from __future__ import print_function
import click
import sys
import os
import time
import tqdm
from filestore import FileStore
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(handler)

DEFAULT_EXT = "pdf;png;jpg;txt"

def typefilter(f):
    global EXTENSIONS
    for ext in EXTENSIONS:
        if f.lower().endswith(ext.lower()):
            return True
    return False

def get_files(directory):
    files = [os.path.join(os.getcwd(), directory, f) for f in \
                                               os.listdir(directory)]
    files = [(hex(hash(os.stat(f))), f) for f in files if typefilter(f)]
    return set(files)

@click.command()
@click.argument("directory",type=click.Path(exists=True))
@click.option("--ptime", default=2.5, help="loop polling interval (default: 2.5s)")
@click.option("--ext", default=DEFAULT_EXT, help='what types to print (default: "pdf;png;jpg;txt")')
@click.option("--log", default="_log", help="directory for archive of printed files (default: _log)")
@click.option("--cmd", default="lp", help="print command to shell out to (default: lp)")
def printd(directory,ptime,ext,log, cmd):
    global EXTENSIONS

    filestore = FileStore("_log")

    logger.info("Watching: " + os.path.join(os.getcwd(), directory))

    EXTENSIONS = ext.split(";")
    logger.info("Extensions: " + str(EXTENSIONS))
    logger.info("Polling interval: " + str(ptime))
    logger.info("Print command: " + cmd)
    previous_set = get_files(directory)
    logger.info("Set: " + str(previous_set))

    while True:
        time.sleep(ptime)
        new_set = get_files(directory)

        deletions = previous_set - new_set
        if deletions:
            for change in deletions:
                previous_set.discard(change)
                logger.info("Deleted: " + str(change))

        changes = new_set - previous_set
        if changes:
            for change in tqdm.tqdm(changes):
                logger.info("Printing... " + str(change[0][-16:]) + " " + str(change[1]))
                filestore.add(change[1])
                ret = os.system('%s "%s"' % (cmd, change[1]))
                if ret:
                   logger.info("Print error: %d" % ret)
                else:
                    logger.info("Print seems to have worked (rc=0)")
                    if os.path.isfile(change[1]):
                        os.remove(change[1])
                    else:
                        logger.info("Error: %s file not found" % change[1])
            previous_set = new_set

if __name__ == "__main__":
    printd()
