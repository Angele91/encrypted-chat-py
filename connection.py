import socket
import threading
import pickle
from message import Message
import nacl.secret
import nacl.utils

class Connection:
    def __init__(self, key, username):
        self.key = key
        self.username = username
        self.connected_usernames = []
        self.connected_sockets = []

    def close_all(self):
        """
        Close all connected sockets and the main socket.

        This function iterates over all connected sockets and closes each one using the `close()` method. 
        It then closes the main socket using the `close()` method.

        Parameters:
            self (ClassName): An instance of the ClassName class.

        Returns:
            None
        """
        for socket in self.connected_sockets:
            socket.close()
        
        self.socket.close()
    
    def get_key(self):
        """
        Returns the value of the key associated with the instance.
        """
        return self.key

    def send_message(self, message: str):
      """
      Sends a message to the connected sockets.

      Args:
          message (str): The message to be sent.

      Returns:
          None
      """
      key = self.get_key()

      if isinstance(key, str):
          key = bytes.fromhex(key)
      
      nonce = nacl.utils.random(nacl.secret.SecretBox.NONCE_SIZE)
      box = nacl.secret.SecretBox(key)
      encrypted = box.encrypt(message.encode(), nonce)
      
      # Send the encrypted message
      serialized_message = pickle.dumps(Message(self.username, encrypted))
      
      for socket in self.connected_sockets:
          socket.sendall(serialized_message)

    def decrypt_message(self, encrypted_message):
        """
        Decrypts an encrypted message using a secret key.

        Parameters:
            encrypted_message (bytes): The encrypted message to be decrypted.

        Returns:
            str: The decrypted message as a string.
        """
        # Convert the key to bytes if it is a string
        key = self.get_key()
        if isinstance(key, str):
            key = bytes.fromhex(key)

        box = nacl.secret.SecretBox(key)
        decrypted_message = box.decrypt(encrypted_message)

        # Return the decrypted message as a string
        return decrypted_message.decode()
    
    def start_listening(self, port):
        """
        Starts listening on a specified port.

        Parameters:
            port (int): The port number to listen on.

        Returns:
            None
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            ip_address = socket.gethostbyname(socket.gethostname())
            self.socket.bind((ip_address, port))
            self.socket.listen()
            thread = threading.Thread(target=self.connection_handler)
            thread.start()
        except Exception as e:
            print(e)
        
    
    def connect(self, ip_address, port):
        """
        Connects to the specified IP address and port.

        Args:
            ip_address (str): The IP address to connect to. If empty or None, the IP address of the local machine will be used.
            port (int): The port number to connect to.

        Returns:
            None
        """
        if ip_address == '' or ip_address == None:
            ip_address = socket.gethostbyname(socket.gethostname())

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((ip_address, port))
        
        # Send handshake
        handshake_message = Message(self.username, self.key, is_handshake=True)
        handshake_message = pickle.dumps(handshake_message)
        self.socket.sendall(handshake_message)

        while True:
            # wait for the response
            data = self.socket.recv(1024)

            # load the response
            obj = pickle.loads(data)

            # check if the handshake was successful
            if obj.message == 'UNAUTHORIZED':
                print("Handshake failed! Unauthorized!")
                self.socket.close()
                break
            else:
                print("Handshake successful!")
                break
        
        self.connected_sockets.append(self.socket)
        thread = threading.Thread(target=self.server_listener)
        thread.start()

              
    def server_listener(self):
        """
        Listens for incoming messages from the server.

        This function continuously listens for incoming messages from the server. It receives data from the socket in chunks of 1024 bytes. If the received data is empty, it prints a message indicating that the connection to the server has been disconnected and breaks out of the loop.

        Parameters:
        - None

        Returns:
        - None
        """
        while True:
            data = self.socket.recv(1024)
            if not data:
              print("Disconnected from server.")
              break

            obj = pickle.loads(data)
            encrypted_message = obj.message
            decrypted_message = self.decrypt_message(encrypted_message)
            print(f"{obj.username}: {decrypted_message}")

    def connection_handler(self):
        """
        Handles the connection with clients.

        The `connection_handler` method is responsible for accepting incoming client connections and initializing the handshake process. It continuously listens for incoming connections and creates a new thread to handle each client connection.

        Parameters:
        - `self`: The current instance of the class.
        
        Returns:
        - None
        
        Raises:
        - Exception: If an error occurs while accepting client connections or initializing the handshake process.
        """
        try:
          while True:
            client_socket, address = self.socket.accept()
            print(f'Connection from {address} has been established!')
            print("Initiating handshake...")
            thread = threading.Thread(target=self.client_handler, args=(client_socket,))
            thread.start()
        except Exception as e:
            print(e)
      
    def is_authorized(self, data):
        """
        Check if the given username is authorized.

        Parameters:
            data (any): The data to be checked.

        Returns:
            bool: True if the username is authorized, False otherwise.
        """
        if data.username in self.connected_usernames:
            return True
        
        return False
    
    def client_handler(self, client_socket):
        """
        Handles communication with a client socket.

        Args:
            client_socket (socket.socket): The socket object representing the client connection.

        Returns:
            None

        Raises:
            None
        """
        while True:
            data = client_socket.recv(1024)

            if not data:
                print(f"Client {client_socket.getpeername()} has disconnected!")
                client_socket.close()
                break
            
            obj = pickle.loads(data)
            
            if obj.is_handshake:
                if obj.message == self.key.hex():
                  print(f"Handshake successful! {obj.username} is now connected!")
                  self.connected_usernames.append(obj.username)
                  self.connected_sockets.append(client_socket)
                  handshake_accepted_message = Message(self.username, self.key, is_handshake=True)
                  handshake_accepted_message = pickle.dumps(handshake_accepted_message)
                  client_socket.sendall(handshake_accepted_message)
                  continue
                else:
                  handshake_rejected_message = Message(self.username, 'UNAUTHORIZED', is_handshake=True)
                  handshake_rejected_message = pickle.dumps(handshake_rejected_message)
                  client_socket.sendall(handshake_rejected_message)
                  client_socket.close()
                  break
            
            if not self.is_authorized(obj):
                client_socket.close()
                continue
              
            encrypted_message = obj.message
            decrypted_message = self.decrypt_message(encrypted_message)
            print(f"{obj.username}: {decrypted_message}")
    