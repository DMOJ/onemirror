import errno
import logging
import os
from itertools import chain
from time import sleep

import re
from dateutil.parser import parse as parse_date

from onemirror.database import OneDriveDatabaseManager
from onemirror.exception import ResyncRequired

logger = logging.getLogger('onemirror')

EPOCH = parse_date('1970-01-01T00:00:00Z')


class OneMirrorUpdate(object):
    def __init__(self, mirror, delta, full_resync=False):
        self.mirror = mirror
        self.delta = delta
        self.session = self.mirror.client.session
        self.local_dir = local = self.mirror.local_path
        self.full_resync = full_resync
        self.exclude = exclude = self.mirror.exclude

        self.name = {}
        self.parent = {}
        self.root = self.mirror.root_id
        self.path_cache = {self.root: ''}
        self.to_delete = []

        self.current = current = set()

        if full_resync:
            for path, dirnames, filenames in os.walk(local):
                dir = os.path.relpath(path, local).replace('\\', '/')
                if dir == '.':
                    for name in chain(dirnames, filenames):
                        if exclude is None or not exclude.match(name):
                            current.add(name)
                else:
                    for name in chain(dirnames, filenames):
                        path = '%s/%s' % (dir, name)
                        if exclude is None or not exclude.match(path):
                            current.add(path)

    def update(self):
        items = 0
        for item in self.delta:
            items += 1
            self.update_item(item)

        self.to_delete.sort(key=len, reverse=True)
        for dir in self.to_delete:
            try:
                os.rmdir(dir)
            except OSError:
                logger.warning('Could not delete non-empty directory: %s', dir)
            else:
                logger.info('Deleted directory: %s', dir)

        if self.full_resync:
            isdir = (errno.EISDIR, errno.EACCES)
            for item in sorted(self.current, key=len, reverse=True):
                path = self.local_path(item)
                try:
                    os.remove(path)
                except OSError as e:
                    if e.errno not in isdir:
                        raise
                    try:
                        os.rmdir(path)
                    except OSError:
                        logger.warning('Could not delete local-only non-empty directory: %s', item)
                    else:
                        logger.info('Deleted local-only directory: %s', item)
                else:
                    logger.info('Deleted local-only file: %s', item)

        return items

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
        return os.path.join(self.local_dir, path)

    def update_item(self, item, EPOCH=EPOCH, EEXIST=errno.EEXIST, ENOENT=errno.ENOENT):
        item_id = item['id']
        self.name[item_id] = item['name']
        self.parent[item_id] = item['parentReference']['id']

        path = self.get_path(item_id)
        if self.exclude is not None and self.exclude.match(path):
            logger.info('Ignore file: %s', path)
            return

        if 'deleted' in item:
            local = self.local_path(path)
            if 'file' in item:
                try:
                    os.remove(local)
                except OSError as e:
                    if e.errno != ENOENT:
                        raise
                logger.info('Deleted file: %s', path)
            else:
                self.to_delete.append(local)
                logger.debug('Queueing for deletion: %s', path)
        elif 'file' in item:
            mtime = round((parse_date(item['lastModifiedDateTime']) - EPOCH).total_seconds(), 2)
            local = self.local_path(path)
            self.current.discard(path)

            if os.path.exists(local):
                stat = os.stat(local)
                if round(stat.st_mtime, 2) == mtime and item['size'] == stat.st_size:
                    logger.debug('Already up-to-date: %s', path)
                    return

            logging.info('Downloading: %s', path)
            self.download(item['@content.downloadUrl'], local)
            os.utime(local, (mtime, mtime))
        elif 'folder' in item:
            self.current.discard(path)
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
        self.local_path = local
        self.remote_path = remote
        self.delta_token = None
        self.interval = kwargs.pop('inteval', 10)
        exclude = kwargs.pop('exclude', None)
        if exclude is not None:
            self.exclude = re.compile(exclude)
        else:
            self.exclude = None

        super(OneDriveMirror, self).__init__(*args, **kwargs)

    def update_token(self, token):
        self.delta_token = self['delta_token'] = token
        self.commit()

    def __enter__(self):
        super(OneDriveMirror, self).__enter__()
        self.delta_token = self['delta_token']
        self.root_id = self.client.metadata(self.remote_path)['id']
        return self

    def update(self):
        full_resync = not self.delta_token
        try:
            delta_viewer = self.client.view_delta(self.remote_path, token=self.delta_token)
        except ResyncRequired:
            self.update_token(None)
            return self.update()
        delta_viewer.token_update = self.update_token

        return OneMirrorUpdate(self, delta_viewer, full_resync).update()

    def run(self):
        while True:
            if self.update() == 0:
                sleep(self.interval)
