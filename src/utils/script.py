"""
Functions about the lifetime of a python script. For e.g. restarting, updating repository etc.
"""
from argparse import ArgumentParser
import sys
import os
import logging



def restart():
    """
    Restart the calling python script with the same arguments as before.
    """
    os.execv(sys.executable, ['python'] + sys.argv)


if __name__=='__main__':
    parser = ArgumentParser()
    parser.add_argument('-r', '--restart', default=False, action='store_true')

    args = parser.parse_args()

    cmd = ' '.join(a for a in sys.argv if a not in ('-r', '--restart'))
    if args.restart:
        logging.warning('Restarting: %s %s' % (sys.executable, cmd))
        os.execv(sys.executable, ['python'] + [a for a in sys.argv if a not in ('-r', '--restart')])
    else:
        logging.warning('Standard process: %s %s' % (sys.executable, ' '.join(sys.argv)))