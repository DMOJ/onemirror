from onemirror.session import OneDriveSessionManager, command_line_auth_handler


def main():
    with OneDriveSessionManager('onedrive.json', '000000004C17987A', 'xk9GckVE6ZUM-rgSmjDx8JuTNvWLXdV3') as client:
        client.refresh()


if __name__ == '__main__':
    main()