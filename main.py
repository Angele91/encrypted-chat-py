import PySimpleGUI as sg
from connection import Connection
import nacl.secret
import nacl.utils

# Define the layout of the chatbox
layout = [
    [sg.Text('Encryption Key:'), sg.Input(key='-KEY-')],
    [sg.Text('Username:'), sg.Input(key='-USERNAME-')],
    [sg.Text('IP Address:'), sg.Input(key='-IP-')],
    [sg.Text('Port:'), sg.Input(key='-PORT-')],
    [sg.Button('Connect', key='-CONNECT-'), sg.Button('Listen', key='-LISTEN-')],
    [sg.Output(size=(50, 10), key='-OUTPUT-')],
    [sg.Input(key='-MESSAGE-'), sg.Button('Send', key='-SEND-')]
]

# Create the window
window = sg.Window('Chatbox', layout)

connection = None

# Event loop to process events
while True:
    event, values = window.read()

    key = values['-KEY-']
    username = values['-USERNAME-'] if values['-USERNAME-'] != '' else 'Anonymous'
    port = values['-PORT-'] if values['-PORT-'] != '' else 1234
    ip_address = values['-IP-']
    message = values['-MESSAGE-']

    # Close the window if the user closes it
    if event == sg.WINDOW_CLOSED:
        if connection != None:
            connection.close_all()
        break

    if event == '-LISTEN-':
        generated_key = nacl.utils.random(nacl.secret.SecretBox.KEY_SIZE)
        connection = Connection(generated_key, username)
        connection.start_listening(port)
        print(f"Listening on {ip_address}:{port}")
        print(f"Encryption key: {generated_key.hex()}")
        continue
    
    if event == '-CONNECT-':
        connection = Connection(key, username)
        connection.connect(ip_address, port)
        continue
    
    if event == '-SEND-':
        if connection == None:
            print("You must connect or listen first!")
            continue
        connection.send_message(message)
        print(f"{username}: {message}")
        window['-MESSAGE-'].update('')
        continue

# Close the window
window.close()
