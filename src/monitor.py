"""
Run a companion server to `controller.py` on a separate machine to receive log
messages sent via HTTP/POST requests.
"""

from flask import request
from dash import Dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px

from utils.logging import get_logger, make_logger
from controller import get_settings, DEFAULTS


dapp = Dash(__name__)   # the Dash application wrapper
app = dapp.server       # The flask app used

dapp.layout = html.Div([
    html.H3('Logs'),
    html.Div(['Hello'])
])


@app.route('/log', methods=('POST',))   # endpoint for POST requests
def log():
    logger = get_logger('monitor')
    logger.info(request.form['msg'])
    return 'OK'



if __name__ == '__main__':
    logger = get_logger('monitor')
    logger = make_logger(enable=('stream',), logger=logger,
        verbosity='INFO', logs_stream_verbosity='INFO')
    dapp.run_server(host='0.0.0.0', port=5000, debug=True)
