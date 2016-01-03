import sqlite3

from onemirror.api import OneDriveClient
from onemirror.session import command_line_auth_handler


class OneDriveDatabaseManager(object):
    def __init__(self, store, client_id, secret, scopes=None, auth_handler=command_line_auth_handler):
        self.conn = sqlite3.connect(store)
        self.cursor = self.conn.cursor()

        self.cursor.execute('CREATE TABLE IF NOT EXISTS map(key TEXT PRIMARY KEY, value TEXT)')

        self.auth_handler = auth_handler
        self.client = OneDriveClient(client_id, secret, scopes)

    def __getitem__(self, item):
        row = self.cursor.execute('SELECT value FROM map WHERE `key` = ?', (item,)).fetchone()
        return None if row is None else row[0]

    def __setitem__(self, key, value):
        self.cursor.execute('REPLACE INTO map (`key`, value) VALUES (?, ?)', (key, value))

    def save(self):
        data = self.client.save()
        self.cursor.executemany('REPLACE INTO map (`key`, value) VALUES (?, ?)', data.iteritems())
        self.commit()

    def commit(self):
        self.conn.commit()

    def all(self):
        return {k: v for k, v in self.cursor.execute('SELECT `key`, value FROM map')}

    def __enter__(self):
        try:
            self.client.load(self.all())
        except (KeyError, ValueError):
            self.client.update_auth_code(self.auth_handler(self.client.auth_code_url))
        else:
            self.client.refresh()
        self.save()
        return self, self.client

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.save()
