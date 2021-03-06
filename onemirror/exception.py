class OneMirrorError(Exception):
    pass


class InvalidDataError(OneMirrorError):
    pass


class InvalidAuthCodeError(InvalidDataError):
    pass


class AuthenticationError(OneMirrorError):
    pass


class ObjectNotFoundError(OneMirrorError):
    pass


class ResyncRequired(OneMirrorError):
    pass
