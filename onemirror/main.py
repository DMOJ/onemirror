from onemirror.api import OneDriveClient


def main():
    client = OneDriveClient('000000004C17987A', 'xk9GckVE6ZUM-rgSmjDx8JuTNvWLXdV3')
    print 'Visit the following URI to authenticate:'
    print client.auth_code_url
    print
    print 'Enter the URL of the blank page:'
    client.update_auth_code(raw_input())
    client.refresh()


if __name__ == '__main__':
    main()