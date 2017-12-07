from socket import *
import ssl #for SSL connection required by Gmail

def send_email(message, email):
        msg = '\r\n %s' % message
        endmsg ='\r\n.\r\n'
        # Choose a mail server (e.g. Google mail server) and call it mailserver
        mailServer = 'smtp.gmail.com'
        port = 587
        ##user credential for gmail
        user = 'bWFkY2hhdHRlcjIwMTdAZ21haWwuY29t' #email = madchatter2017@gmail.com
        password = 'cmJyYW96dGNlY3Bta210bQ==' 
        ##connection
        mySocket = socket(AF_INET, SOCK_STREAM)
        mySocket.connect((mailServer, port))
        recv = mySocket.recv(1024).decode('utf-8')
        print(recv)
        if recv[:3] != '220':
            print ('220 reply not received from server.\n')
        else:
            print ('Initial connection established\n')
            

        # Send EHLO command and print server response.
        print('Sending EHLO command to server.\n')
        heloCommand = 'EHLO smtp.google.com\r\n'
        mySocket.send(bytes(heloCommand, 'utf-8'))
        recv1 = mySocket.recv(1024).decode('utf-8')
        print(recv1)
        if recv1[:3] != '250':
            print ('250 reply not received from server.\n')
        else:
            print ('Server responded to EHLO\n')

        # Request TLS
        print('Starting TLS connection\n')
        mySocket.sendall(bytes('STARTTLS\r\n','utf-8'))
        tlsRecv = mySocket.recv(1024).decode('utf-8')
        print(tlsRecv)
        if tlsRecv[:3] != '220':
            print ('220 reply not received from server\n')
        else:
            print ('TLS connection established\n')
        # SSL
        mySSL = ssl.wrap_socket(mySocket, ssl_version=ssl.PROTOCOL_SSLv23)
        # Authorization
        print('Begin authorization.\n')
        authCommand = ('AUTH LOGIN %s\r\n' % user)
        mySSL.sendall(bytes(authCommand, 'utf-8'))
        authRecv = mySSL.recv(1024).decode('utf-8')
        print(authRecv)
        if authRecv[:3] != '334':
            print('334 reply not received from server.\n')
        else:
            print('Server accepts authorization request.\n')
        mySSL.sendall(bytes('%s\r\n' % password, 'utf-8'))
        authRecv2 = mySSL.recv(1024).decode('utf-8')
        print(authRecv2)
        if authRecv2[:3] != '235':
            print('235 reply not received from server.\n')
        else:
            print('Password accepted\n')
            

        # Send MAIL FROM command and print server response.
        mySSL.sendall(bytes('MAIL FROM:<madchatter2017@gmail.com>\r\n', 'utf-8'))
        recv2 = mySSL.recv(1024).decode('utf-8')
        print(recv2) ##printing response
        if recv2[:3] != '250':
            print ('250 reply not received from server.\n')
         
        # Send RCPT TO command and print server response.
        mySSL.sendall(bytes('RCPT TO:<%s>\r\n' % email, 'utf-8'))
        recv3 = mySSL.recv(1024).decode('utf-8')
        print(recv3) ##printing response
        if recv3[:3] != '250':
            print ('250 reply not received from server.\n')
         

        # Send DATA command and print server response.
        mySSL.sendall(bytes('DATA\r\n', 'utf-8'))
        recv4 = mySSL.recv(1024).decode('utf-8')
        print(recv4) ##printing response
        if recv4[:3] != '250':
         print('250 reply not received from server.\n')
         

        # Send message data + ending message
        mySSL.sendall(bytes(msg + '\r\n.\r\n', 'utf-8'))
        recv5 = mySSL.recv(1024).decode('utf-8')
        print(recv5) ##printing response
        if recv5[:3] != '250':
            print ('250 reply not received from server.')
            

        # Send QUIT command and get server response.
        mySSL.sendall(bytes('QUIT\r\n', 'utf-8'))
        recv6 = mySSL.recv(1024).decode('utf-8')
        print(recv6) ##printing response
        if recv6[:3] != '250':
            print('250 reply not received from server.')

