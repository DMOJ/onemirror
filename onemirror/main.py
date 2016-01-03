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
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG)
    with OneDriveMirror(args.local, args.remote, args.database, args.client_id, args.secret) as mirror:
        mirror.run()


if __name__ == '__main__':
    main()
