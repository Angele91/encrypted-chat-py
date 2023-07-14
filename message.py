class Message:
    def __init__(self, username, message, is_handshake=False):
        self.username = username
        self.message = message
        self.is_handshake = is_handshake
