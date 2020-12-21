"""
Various classes to be used by `logging.Logger` for sending messages:

* Formatters convert a message `logging.LogRecord` object into a string for output
* Handlers direct a message to various outputs (stream, HTTP, file)
"""
import sys
import logging
from logging.handlers import HTTPHandler, BufferingHandler
import smtplib
import email
import time
from typing import Dict
from urllib.parse import urlparse



def get_logger(name: str=None) -> logging.Logger:
    return logging.getLogger(__name__ if name is None else name)



def make_logger(enable='all', logger=None, formatter=None, **settings) -> logging.Logger:
    logging.captureWarnings(True)
    logger = get_logger() if logger is None else logger
    logger.setLevel(settings['verbosity'])
    if not isinstance(formatter, logging.Formatter):
        formatter = logging.Formatter('%(asctime)s, %(levelname)s, %(message)s',
                                      datefmt='%Y-%m-%d %H:%M:%S')

    # File logging
    if enable=='all' or 'file' in enable:
        handler_file = logging.FileHandler(filename=settings['logs'], mode='a')
        handler_file.setFormatter(formatter)
        handler_file.setLevel(settings['logs_file_verbosity'])
        logger.addHandler(handler_file)

    # Stream logging
    if enable=='all' or 'stream' in enable:
        handler_stream = logging.StreamHandler(stream=sys.stderr)
        handler_stream.setFormatter(formatter)
        handler_stream.setLevel(settings['logs_stream_verbosity'])
        logger.addHandler(handler_stream)

    # HTTP Logging
    if enable=='all' or 'http' in enable:
        remote_log = settings.get('logs_server')
        remote_verbosity = settings.get('logs_server_verbosity')
        if remote_log not in ('', None) and remote_verbosity not in ('', None):
            parsed = urlparse(remote_log)
            handler_remote = RemoteHandler(host=parsed.netloc, url=parsed.path, method='POST')
            handler_remote.setLevel(remote_verbosity)
            logger.addHandler(handler_remote)

    # Email logging
    if enable=='all' or 'email' in enable:
        mailhost = settings.get('logs_email_smtp_server')
        fromaddr = settings.get('logs_email_from')
        toaddrs = settings.get('logs_email_to', '')
        username = settings.get('logs_email_username')
        password = settings.get('logs_email_password')
        email_verbosity = settings.get('logs_email_verbosity')
        name = settings.get('controller', '') + settings.get('application', '')

        if (email_verbosity not in ('', None) and \
            mailhost not in ('', None) and \
            fromaddr not in ('', None) and \
            len(toaddrs) > 0 and toaddrs[0]!='' and \
            username not in ('', None) and password not in ('', None)):
            
            logger.info('Setting up email logging.')   
            handler_email = EmailHandler(name, mailhost, fromaddr, toaddrs,
                username, password, capacity=settings['logs_email_batchsize'],
                logger=logger)
            handler_email.setLevel(email_verbosity)
            handler_email.setFormatter(formatter)
            logger.addHandler(handler_email)
        else:
            logger.info('Skipping email logging.')

    return logger



class EmailHandler(BufferingHandler):
    """
    Accumulates log records for some time and sends them as an email when capacity
    is reached or when a particular severity level is reached.

    Attributes
    ----------
    smtp: smtplib.SMTP
        The email server instance
    buffer: List
        A list of logging.LogRecord messages
    """


    def __init__(self, name: str, mailhost: str, fromaddr: str, toaddrs: list,
            username: str, password: str, capacity: int,
            flushLevel:str=logging.CRITICAL, logger: logging.Logger=None):
        """

        Parameters
        ----------
        name : str
            The name to use in the email subject
        mailhost : str
            The hostname of the smtp email server sending emails
        fromaddr : str
            The address to send the email from
        toaddrs : list
            A list of addresses to send the email to
        username : str
            username for logging into the email server
        password : str
            Password for logging into the email server
        capacity : int
            Maximum number of messages to buffer before sending them in one email
        flushLevel : str, optional
            Severity of message which triggers email, by default logging.CRITICAL
        logger : logging.Logger, optional
            A logger to log setup of this instance to, by default None
        """
        super().__init__(capacity)
        self.name = name
        self.fromaddr = fromaddr
        self.toaddrs = toaddrs
        self.flushLevel = flushLevel
        self.smtp = smtplib.SMTP(mailhost, smtplib.SMTP_PORT)
        self.smtp.starttls()
        if isinstance(logger, logging.Logger):
            logger.info(self.smtp.login(username, password))


    def flush(self):
        """
        Compose and send the email message.
        """
        maxlevel = max(self.buffer, key=lambda r: r.levelno).levelname
        
        msg = email.message.EmailMessage()
        msg['from'] = self.fromaddr
        msg['to'] = self.toaddrs
        msg['subject'] = self.name + ' - ' + maxlevel
        msg_str = ''
        for record in self.buffer:
            msg_str += self.format(record) + '\n'
        msg.set_content(msg_str)
        self.smtp.send_message(msg)
        super().flush()


    def shouldFlush(self, record) -> bool:
        """
        Given the latest message record, determines if email should be triggered
        or not.

        Parameters
        ----------
        record : logging.LogRecord
            The latest log message

        Returns
        -------
        bool
            True if email should be triggered.
        """
        return super().shouldFlush(record) or record.levelno >= self.flushLevel



class RemoteHandler(HTTPHandler):
    """
    Logging Handler to send HTTP requests to a server.
    """


    def mapLogRecord(self, record: logging.LogRecord) -> Dict[str, str]:
        """
        Converts a logging.LogRecord message into a dictionary which is sent
        as an encoded URL (GET) or a form (POST) to the server.

        Parameters
        ----------
        record : logging.LogRecord
            The latest message log

        Returns
        -------
        Dict[str, str]
            A dictionary to encode into a HTTP request.
        """
        return super().mapLogRecord(record)



class UTCFormatter(logging.Formatter):
    """
    A formatter which uses UTC time (instead of local time) as default.
    """

    converter = time.gmtime
