import json
import time
from urlparse import urlparse, parse_qs

import requests

from onemirror.exception import InvalidAuthCodeError, AuthenticationError


class OneDriveClient(object):
    DEFAULT_SCOPES = ['onedrive.readonly', 'wl.signin', 'wl.offline_access']
    DESKTOP_REDIRECT = 'https://login.live.com/oauth20_desktop.srf'

    def __init__(self, client_id, secret, scopes=None):
        self.client_id = client_id
        self.client_secret = secret

        if scopes is None:
            self.scopes = self.DEFAULT_SCOPES
        else:
            self.scopes = scopes

        self.session = requests.Session()

        self.user_id = None
        self.access_token = None
        self.refresh_token = None
        self.expires = None

        self.headers = {}

    @property
    def auth_code_url(self):
        return self.session.get('https://login.live.com/oauth20_authorize.srf', params={
            'client_id': self.client_id, 'response_type': 'code', 'scope': ' '.join(self.scopes),
            'redirect_uri': self.DESKTOP_REDIRECT
        }).url

    def update_auth_code(self, url):
        try:
            result = parse_qs(urlparse(url).query)
            self._redeem(result['code'][0])
        except (KeyError, IndexError):
            raise InvalidAuthCodeError('Couuld not find a valid auth code in: %s' % url)

    def _redeem(self, code):
        result = self.session.post('https://login.live.com/oauth20_token.srf', data={
            'client_id': self.client_id, 'redirect_uri': self.DESKTOP_REDIRECT,
            'client_secret': self.client_secret, 'code': code,
            'grant_type': 'authorization_code'
        }).json()
        self._update_token(result)

    def refresh(self):
        result = self.session.post('https://login.live.com/oauth20_token.srf', data={
            'client_id': self.client_id, 'redirect_uri': self.DESKTOP_REDIRECT,
            'client_secret': self.client_secret, 'refresh_token': self.refresh_token,
            'grant_type': 'refresh_token'
        }).json()
        self._update_token(result)

    def _update_token(self, result):
        if 'error' in result:
            raise AuthenticationError(result['error_description'])

        if 'user_id' in result:
            self.user_id = result['user_id']

        self.access_token = result['access_token']
        self.refresh_token = result['refresh_token']

        if 'expires_in' in result:
            self.expires = time.time() + result['expires_in']
        elif 'expires' in result:
            self.expires = result['expires']

        self.session.headers['Authorization'] = 'bearer ' + self.access_token

    def logout(self):
        self.session.get('https://login.live.com/oauth20_logout.srf', params={
            'client_id': self.client_id, 'redirect_uri': self.DESKTOP_REDIRECT
        })

    def save(self):
        return json.dumps({
            'access_token': self.access_token, 'refresh_token': self.refresh_token,
            'expires': self.expires, 'user_id': self.user_id
        }, encoding='utf-8')

    def load(self, data):
        if hasattr(data, 'read'):
            data = json.load(data, encoding='utf-8')
        elif not isinstance(data, dict):
            data = json.loads(data, encoding='utf-8')
        self._update_token(data)
