from flask import Flask, render_template, request, redirect, session, url_for
import pymysql.cursors
from hashlib import sha1
from functools import wraps
from socket import *
import ssl #for SSL connection required by Gmail
import random #for password generator

app = Flask(__name__)

#Connect to MadChatter DB
conn = pymysql.connect(host='localhost',
	port=3306,
	user='root',
	password='',
	db='MadChatter',
	charset='utf8mb4',
	cursorclass=pymysql.cursors.DictCursor)

@app.route("/")
def main():
	return render_template('index.html')

@app.route("/login")
def login():
	return render_template('login.html')

#wrap around functions that are only available to logged in users
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            return render_template('login.html')
    return wrap

@app.route("/register")
def register():
	return render_template('register.html')

@app.route("/home")
@login_required
def home():
	username = session['username']
	cursor = conn.cursor();
	query = 'SELECT timest,file_path,content_name FROM content WHERE username = %s OR public = 1 ORDER BY timest DESC'
	cursor.execute(query, (username))
	data = cursor.fetchall()
	cursor.close()
	return render_template('home.html', username=username, posts=data)

#Register new user
@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
	#pull info from registration page
	username = request.form['username']
	password = request.form['password']
	fname = request.form['first_name']
	lname = request.form['last_name']
	email = request.form['email']

	cursor = conn.cursor()
	#Check for existance of new user
	query = 'SELECT * FROM person WHERE username = %s'
	cursor.execute(query, (username))
	print ("existence check complete")
	data = cursor.fetchone()
	err = None
	if(data):
		error = "The user "+username+" already exists"
		return render_template('register.html', error = err)
	else:
		ins = 'INSERT INTO person (username,password,first_name,last_name,email) VALUES(%s, sha1(%s), %s, %s, %s)'
		cursor.execute(ins, (username, password.encode(), fname, lname, email))
		conn.commit()
		cursor.close()
		return render_template('index.html')

#log in user
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
	#grabs information from the forms

	username = request.form['username']
	password = request.form['password']

	#retrieves username and password
	cursor = conn.cursor()
	query = 'SELECT password FROM person WHERE username = %s AND password = sha1(%s)'
	cursor.execute(query, (username, password.encode()))
	data = cursor.fetchone()
	cursor.close()
	error = None
	if(data):
		#creates a session for the the user
		session['username'] = username
		session['logged_in'] = True
		return redirect(url_for('home'))
	else:
		#returns an error message to the html page
		error = 'Invalid login or username'
		return render_template('login.html', error=error)


@app.route('/resetPassword', methods=['POST'])
def resetPassword():
	return redirect('/')
        
@app.route('/mailPassword', methods=['GET', 'POST'])
def mailPassword(new_pw, email):
        msg = '\r\n Your temporary password is: %s!' % new_pw
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

def checkAccount(username, email):
        inst = 'SELECT * FROM person WHERE username = %s AND email = %s'
        cursor = conn.cursor()
        cursor.execute(inst, (username, email))
        data = cursor.fetchone()
        cursor.close()
        #if account exists, send email
        if data:
                email = data['email']
                new_pw = '123123123'
                inst = 'UPDATE person SET password = sha1(%s) WHERE username = %s AND email = %s'
                cursor = conn.cursor()
                cursor.execute(inst, (new_pw, username, email))
                conn.commit()
                cursor.close()
                mailPassword(new_pw, email)
                return 'Password reset was successful, new password has been mailed to your email!'
        #if account doesn't exist, return 0
        else:
                return 'Email cannot be found'
@app.route('/view', methods=['GET'])
@login_required
def view():
        username = session['username']
        inst = "SELECT * FROM content WHERE content.username = %s"
        inst2 = "SELECT * FROM content WHERE content.public = 1"
        cursor = conn.cursor()
        cursor.execute(inst, (username))
        user_contents = cursor.fetchall()
        cursor.close()
        ##
        cursor = conn.cursor()
        cursor.execute(inst2)
        avail_contents = cursor.fetchall()
        cursor.close()
        return render_template('view.html', user_contents=user_contents, avail_contents=avail_contents)

@app.route('/post', methods=['GET', 'POST'])
@login_required
def post():
	username = session['username']
	cursor = conn.cursor();
	content = request.form['content']
	description = request.form['description']
	public = request.form['makePublic']
	if(public != '1'):
		public = '0'
	query = 'INSERT INTO content (username,file_path,content_name,public) VALUES(%s, %s, %s, %s)'
	cursor.execute(query, (username,content,description,public))
	data = cursor.fetchall()
	conn.commit()
	cursor.close()
	return redirect(url_for('home'), posts=data)

@app.route('/comment/<content_id>', methods = ['GET', 'POST'])
def comment(content_id): #need to divide into 2 html files
        username = session['username']
        comment = request.form['comment']
        cursor = conn.cursor();
        inst = 'INSERT INTO TABLE comment(id, username, comment_text) VALUES (%s, %s, %s)'
        cursor.execute(inst, (content_id, username, comment))
        conn.commit()
        conn.close()
        return redirect(url_for('/view'))

@app.route('/')
        
@app.route('/logout')
def logout():
	session.pop('username')
	return redirect('/')

app.secret_key = 'some key that you will never guess'

if __name__ == "__main__":
		app.run(debug=True)


