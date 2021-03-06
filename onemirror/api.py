import time
from urlparse import urlparse, parse_qs

import requests

from onemirror.exception import InvalidAuthCodeError, AuthenticationError, ObjectNotFoundError, ResyncRequired


class OneDriveClient(object):
    DEFAULT_SCOPES = ['onedrive.readonly', 'wl.signin', 'wl.offline_access']
    DESKTOP_REDIRECT = 'https://login.live.com/oauth20_desktop.srf'
    API_ROOT = 'https://api.onedrive.com/v1.0'

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
            self.expires = time.time() + result['expires_in'] - 60
        elif 'expires' in result:
            self.expires = result['expires']

        self.session.headers['Authorization'] = 'bearer ' + self.access_token

    def logout(self):
        self.session.get('https://login.live.com/oauth20_logout.srf', params={
            'client_id': self.client_id, 'redirect_uri': self.DESKTOP_REDIRECT
        })

    def save(self):
        return {
            'access_token': self.access_token, 'refresh_token': self.refresh_token,
            'expires': self.expires, 'user_id': self.user_id
        }

    def load(self, data):
        self._update_token(data)

    def _renew(self):
        if time.time() >= self.expires:
            self.refresh()

    def drives(self):
        self._renew()
        return self.session.get('%s/drives' % self.API_ROOT).json()

    def metadata(self, path):
        self._renew()
        return self.session.get('%s/drive/root:%s' % (self.API_ROOT, path)).json()

    def view_delta(self, path, url=None):
        self._renew()
        if url is None:
            url = '%s/drive/root:%s:/view.delta' % (self.API_ROOT, path)
        request = self.session.get(url)
        data = request.json()
        if 'error' in data:
            if data['error']['code'] == 'resyncRequired':
                raise ResyncRequired()
            raise ObjectNotFoundError(data['error']['message'])
        return DeltaViewer(request.json(), self.session)


class DeltaViewer(object):
    def __init__(self, data, session):
        self.data = data
        self.session = session
        self.new_delta = None

    def __iter__(self):
        while True:
            if 'error' in self.data:
                if self.data['error']['code'] == 'resyncRequired':
                    raise ResyncRequired()
                raise ObjectNotFoundError(self.data['error']['message'])
            for item in self.data['value']:
                yield item
            if '@odata.deltaLink' in self.data:
                if self.new_delta:
                    self.new_delta(self.data['@odata.deltaLink'])
                break
            self.data = self._next_page()

    def _next_page(self):
        resp = self.session.get(self.data['@odata.nextLink'])
        if resp.status_code != 200:
            print resp.headers, resp.text
            try:
                retry = int(resp.headers['retry-after'])
            except (KeyError, ValueError):
                retry = 20
            time.sleep(retry)
            return self._next_page()
        return resp.json()
