# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import io
import os
import datetime
from app_config import ConfigManager

class UserLogger(object):
    def __init__(self, log_name=None):
        if log_name is None:
            try:
                cfg = ConfigManager()
                log_name = cfg.get('log_name', 'quadrillageauto.log')
            except Exception:
                log_name = 'quadrillageauto.log'
        self.log_dir = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'pyRevit', 'KajizmoRevit', 'logs')
        try:
            if not os.path.exists(self.log_dir):
                os.makedirs(self.log_dir)
        except Exception:
            self.log_dir = os.path.dirname(__file__)
        self.log_path = os.path.join(self.log_dir, log_name)
        try:
            self.username = os.environ.get('USERNAME') or os.environ.get('USER') or 'Unknown'
        except Exception:
            self.username = 'Unknown'

    def _write(self, level, message):
        try:
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            line = u"[{}] [{}] [{}] {}\n".format(timestamp, self.username, level, message)
            with io.open(self.log_path, 'a', encoding='utf-8') as f:
                f.write(line)
        except Exception:
            pass

    def info(self, message):
        self._write('INFO', message)

    def warning(self, message):
        self._write('WARNING', message)

    def error(self, message):
        self._write('ERROR', message)
