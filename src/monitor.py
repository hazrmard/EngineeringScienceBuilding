"""
Run a companion server to `controller.py` on a separate machine to receive log
messages sent via HTTP/POST requests.
"""

from argparse import ArgumentParser, Namespace
import logging

from flask import request
from dash import Dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px

from utils.logging import get_logger, make_logger
from controller import get_settings, DEFAULTS

DEFAULTS['host'] = '0.0.0.0'
DEFAULTS['port'] = 5000


dapp = Dash(__name__)   # the Dash application wrapper
app = dapp.server       # The flask app used

dapp.layout = html.Div([
    html.H3('Logs'),
    html.Div(['Hello'])
])


@app.route('/log', methods=('POST',))   # endpoint for POST requests
def log():
    logger = get_logger()
    rdict = request.form
    ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    logger.log(int(rdict.get('levelno', logging.ERROR)), 'From: %s. %s' % (ip, rdict.get('message',
                                                                               rdict.get('msg', 'NO_MESSAGE'))))
    return 'OK'



def make_arguments() -> ArgumentParser:
    # If a setting can be overridden by the settings ini file, then the default
    # should be None. This is because get_settings() assumes a non-None value
    # means that the setting was explicitly provided as a flag in the command
    # line and should not be changed.
    # Actual default values should be stored as variables (DEFAULTS), or put in
    # the settings ini file.
    parser = ArgumentParser(description='Monitor for condenser set-point optimization script.',
        epilog='Additional settings can be changed from the specified settings ini file.')
    parser.add_argument('-s', '--settings', type=str, required=False,
                        help='Location of settings file.', default=DEFAULTS['settings'])
    parser.add_argument('-l', '--logs', type=str, required=False, default=None,
                        help='Location of file to write logs to.')
    parser.add_argument('-p', '--port', type=int, required=False, default=None,
                        help='Port number of server to listen on.')
    parser.add_argument('--host', type=str, required=False, default=None,
                        help='Host address of server to listen on. e.g. 0.0.0.0')
    parser.add_argument('-v', '--verbosity', type=str, required=False, default=None,
                        help='Verbosity level.',
                        choices=('CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'))
    parser.add_argument('-m', '--message', type=str, required=False, default=None,
                        help=('Compose a test INFO message to send to a running monitor.'))
    return parser



if __name__ == '__main__':
    parser = make_arguments()
    args = parser.parse_args()
    if args.message is not None:
        settings = get_settings(args, section='DEFAULT')
        logger = get_logger()
        logger = make_logger(enable=('stream', 'email', 'http'), logger=logger, **settings)
        logger.info(args.message)
    else:
        settings = get_settings(args, section='MONITOR')
        logger = get_logger()
        logger = make_logger(enable=('stream', 'file'), logger=logger, **settings)
        logger.info('Started monitoring on %s:%s ...' % (settings['host'], settings['port']))
        dapp.run_server(host=settings['host'], port=settings['port'], debug=True)
