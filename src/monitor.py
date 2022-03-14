"""
Run a companion server to `controller.py` on a separate machine to receive log
messages sent via HTTP/POST requests.
"""

from argparse import ArgumentParser, Namespace
import logging

from flask import request
from dash import Dash
from dash import html, dcc
import plotly.express as px
import pandas as pd
import numpy as np

from utils.logs import get_logger, make_logger
from controller import get_settings, DEFAULTS

DEFAULTS['host'] = '0.0.0.0'
DEFAULTS['port'] = 5000


dapp = Dash(__name__)   # the Dash application wrapper
app = dapp.server       # The flask app used

styles = {
    'pre': {
        'border': 'thin lightgrey solid',
        'overflowX': 'scroll'
    }
}
df = pd.DataFrame({
    # "x": [1,2,1,2],
    "x": np.random.randint(55, 75, size=20),
    "y": np.random.randint(55, 75, size=20),
    # "y": [1,2,3,4],
    "customdata": np.arange(20),
    # "status": ["nominal", "anomalous", "nominal", "anomalous"]
    "status": np.random.choice(["nominal", "anomalous"], size=20, replace=True)
})

fig = px.scatter(df, x="x", y="y", color="status", custom_data=["customdata"])

fig.update_layout(clickmode='event+select')

fig.update_traces(marker_size=20)


with open('../logs.txt', 'r') as f:
    lines = f.readlines(5000)
dapp.layout = html.Div([
    html.H3('Cooling Tower Control Logs'),
    html.Textarea('\n'.join(lines), cols=128, rows=24),
    html.H3(['Action setpoints']),
    html.H3(['Anomalies']),
    dcc.Graph(
        id='basic-interactions',
        figure=fig
    )
])


@app.route('/log', methods=('POST',))   # endpoint for POST requests
def log():
    logger = get_logger('monitor')
    rdict = request.form    # dictionary with keys as logging.LogRecord
    name = rdict.get('name', '')
    message = rdict.get('message', rdict.get('msg', 'NO_MESSAGE'))
    ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    loglevel = int(rdict.get('levelno', logging.ERROR))
    logger.log(loglevel, 'From: %s %s, %s' % (ip, name, message))
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
        logger = get_logger('monitor')
        logger = make_logger(enable=('stream', 'file', 'email', 'http'), logger=logger, **settings)
        logger.info(args.message)
    else:
        settings = get_settings(args, section='MONITOR')
        logger = get_logger('monitor')
        logger = make_logger(enable=('stream', 'file'), logger=logger, **settings)
        logger.info('Started monitoring on %s:%s ...' % (settings['host'], settings['port']))
        dapp.run_server(host=settings['host'], port=settings['port'], debug=True)
