import logging
from logging.handlers import HTTPHandler, BufferingHandler, HTTPHandler
import smtplib
import email
import time
from typing import Dict



class EmailHandler(BufferingHandler):
    
    
    def __init__(self, name, mailhost, fromaddr, toaddrs, username, password,
            capacity, flushLevel=logging.CRITICAL, logger: logging.Logger=None):
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


    def shouldFlush(self, record):
        return super().shouldFlush(record) or record.levelno >= self.flushLevel



class RemoteHandler(HTTPHandler):


    def mapLogRecord(self, record: logging.LogRecord) -> Dict[str, str]:
        return super().mapLogRecord(record)



class UTCFormatter(logging.Formatter):

    converter = time.gmtime
