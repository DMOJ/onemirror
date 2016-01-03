import logging
import os

from datetime import datetime

import errno

from onemirror.database import OneDriveDatabaseManager
from onemirror.exception import ResyncRequired

logger = logging.getLogger('onemirror')

EPOCH = datetime(1970, 1, 1)


class OneMirrorUpdate(object):
    def __init__(self, mirror, delta):
        self.mirror = mirror
        self.delta = delta
        self.session = self.mirror.client.session

        self.name = {}
        self.parent = {}
        self.root = self.mirror.root_id
        self.path_cache = {self.root: ''}

    def update(self):
        for item in self.delta:
            self.update_item(item)

    def get_path(self, id):
        if id in self.path_cache:
            return self.path_cache[id]
        if self.parent[id] == self.root:
            path = self.name[id]
        else:
            path = '%s/%s' % (self.get_path(self.parent[id]), self.name[id])
        self.path_cache[id] = path
        return path

    def local_path(self, path):
        return os.path.join(self.mirror.local_path, path)

    def update_item(self, item, EPOCH=EPOCH, EEXIST=errno.EEXIST):
        item_id = item['id']
        self.name[item_id] = item['name']
        self.parent[item_id] = item['parentReference']['id']

        path = self.get_path(item_id)

        if 'file' in item:
            last_modify = datetime.strptime(item['lastModifiedDateTime'], '%Y-%m-%dT%H:%M:%S.%fZ')
            mtime = round((last_modify - EPOCH).total_seconds(), 2)
            size = item['size']
            download = item['@content.downloadUrl']
            local = self.local_path(path)

            if os.path.exists(local):
                stat = os.stat(local)
                if round(stat.st_mtime, 2) == mtime and size == stat.st_size:
                    logger.debug('Already up-to-date: %s', path)
                    return

            logging.info('Downloading: %s', path)
            self.download(download, local)
            os.utime(local, (mtime, mtime))
        elif 'folder' in item:
            try:
                os.mkdir(self.local_path(path))
            except OSError as e:
                if e.errno != EEXIST:
                    raise
            else:
                logging.info('Creating directory: %s', path)

    def download(self, url, path):
        response = self.session.get(url, stream=True)
        with open(path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=131072):
                if chunk:
                    f.write(chunk)


class OneDriveMirror(OneDriveDatabaseManager):
    def __init__(self, local, remote, *args, **kwargs):
        super(OneDriveMirror, self).__init__(*args, **kwargs)
        self.local_path = local
        self.remote_path = remote
        self.delta_token = None

    def update_token(self, token):
        self.delta_token = self['delta_token'] = token
        self.commit()

    def __enter__(self):
        super(OneDriveMirror, self).__enter__()
        self.delta_token = self['delta_token']
        self.root_id = self.client.metadata(self.remote_path)['id']
        return self

    def update(self):
        try:
            delta_viewer = self.client.view_delta(self.remote_path, token=self.delta_token)
        except ResyncRequired:
            self.update_token(None)
            return self.update()
        delta_viewer.token_update = self.update_token

        OneMirrorUpdate(self, delta_viewer).update()

    def run(self):
        self.update()
