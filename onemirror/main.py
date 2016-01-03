import argparse

from onemirror.database import OneDriveDatabaseManager


def main():
    parser = argparse.ArgumentParser(description='OneDrive mirroring program: create a complete '
                                                 'mirror of OneDrive contents')
    parser.add_argument('remote', nargs='?', default='/')
    parser.add_argument('local', nargs='?', default='OneDrive')
    parser.add_argument('database', nargs='?', default='onedrive.db')
    parser.add_argument('--client-id', default='000000004C17987A')
    parser.add_argument('--secret', default='xk9GckVE6ZUM-rgSmjDx8JuTNvWLXdV3')
    args = parser.parse_args()

    with OneDriveDatabaseManager(args.database, args.client_id, args.secret) as (store, client):
        for i in client.view_delta('/'):
            __import__('pprint').pprint(i)


if __name__ == '__main__':
    main()
