import argparse
import logging

from onemirror.mirror import OneDriveMirror


def main():
    parser = argparse.ArgumentParser(description='OneDrive mirroring program: create a complete '
                                                 'mirror of OneDrive contents')
    parser.add_argument('remote', nargs='?', default='/')
    parser.add_argument('local', nargs='?', default='OneDrive')
    parser.add_argument('database', nargs='?', default='onedrive.db')
    parser.add_argument('--client-id', default='000000004C17987A')
    parser.add_argument('--secret', default='xk9GckVE6ZUM-rgSmjDx8JuTNvWLXdV3')
    parser.add_argument('--interval', default=10, type=int)
    parser.add_argument('--full-update', default=3600, type=int)
    parser.add_argument('-x', '--exclude')
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(asctime)s %(module)s %(message)s')
    with OneDriveMirror(args.local, args.remote, args.database, args.client_id, args.secret,
                        interval=args.interval, exclude=args.exclude, full_update=args.full_update) as mirror:
        mirror.run()


if __name__ == '__main__':
    main()
