from onemirror.database import OneDriveDatabaseManager


def main():
    with OneDriveDatabaseManager('onedrive.db', '000000004C17987A', 'xk9GckVE6ZUM-rgSmjDx8JuTNvWLXdV3') \
            as (store, client):
        for i in client.view_delta('/'):
            __import__('pprint').pprint(i)


if __name__ == '__main__':
    main()
