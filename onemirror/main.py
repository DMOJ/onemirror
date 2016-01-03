from onemirror.session import OneDriveSessionManager, command_line_auth_handler


def main():
    with OneDriveSessionManager('onedrive.json', '000000004C17987A', 'xk9GckVE6ZUM-rgSmjDx8JuTNvWLXdV3') as client:
        for i in client.view_delta('/problems'):
            __import__('pprint').pprint(i)


if __name__ == '__main__':
    main()