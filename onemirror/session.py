import json

from onemirror.api import OneDriveClient


def command_line_auth_handler(url):
    print 'Visit the following URI to authenticate:'
    print url
    print
    print 'Enter the URL of the blank page:'
    return raw_input()


class OneDriveSessionManager(object):
    def __init__(self, store, client_id, secret, scopes=None, auth_handler=command_line_auth_handler):
        self.store = store
        self.auth_handler = auth_handler
        self.client = OneDriveClient(client_id, secret, scopes)

    def __enter__(self):
        try:
            with open(self.store) as f:
                self.client.load(f)
        except (IOError, ValueError):
            self.client.update_auth_code(self.auth_handler(self.client.auth_code_url))
        return self.client

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            with open(self.store, 'w') as f:
                f.write(json.dumps(self.client.save(), encoding='utf-8'))
        except IOError:
            print 'Failed to save state'
