"""
Run a companion server to `controller.py` on a separate machine to receive log
messages sent via HTTP/POST requests.
"""

from argparse import ArgumentParser, Namespace

from flask import request
from dash import Dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px

from utils.logging import get_logger, make_logger
from controller import get_settings, DEFAULTS

DEFAULTS['logs_server'] = 'http://127.0.0.1:5000/log'


dapp = Dash(__name__)   # the Dash application wrapper
app = dapp.server       # The flask app used

dapp.layout = html.Div([
    html.H3('Logs'),
    html.Div(['Hello'])
])


@app.route('/log', methods=('POST',))   # endpoint for POST requests
def log():
    logger = get_logger('monitor')
    rdict = request.form
    logger.log(int(rdict['levelno']), rdict['message'])
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
    parser.add_argument('-r', '--logs-server', type=str, required=False, default=None,
                        help='http://host[:port][/path] of remote server to POST logs to.')
    parser.add_argument('-v', '--verbosity', type=str, required=False, default=None,
                        help='Verbosity level.',
                        choices=('CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'))
    return parser



if __name__ == '__main__':
    parser = make_arguments()
    args = parser.parse_args()
    settings = get_settings(args, section='MONITOR')
    logger = get_logger('monitor')
    logger = make_logger(enable=('stream', 'file', 'email'), logger=logger, **settings)
    logger.info('Started monitoring...')
    dapp.run_server(host=settings['host'], port=settings['port'], debug=True)
