from flask import Flask, render_template, request, redirect, session, url_for
import pymysql.cursors
from hashlib import sha1

app = Flask(__name__)

#Connect to MadChatter DB
conn = pymysql.connect(host='localhost',
	port=8889,
	user='root',
	password='root',
	db='MadChatter',
	charset='utf8mb4',
	cursorclass=pymysql.cursors.DictCursor)

@app.route("/")
def main():
	return render_template('index.html')

@app.route("/login")
def login():
	return render_template('login.html')

@app.route("/register")
def register():
	return render_template('register.html')

@app.route("/home.html")
def home():
	return render_template('home.html')

#Register new user
@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():

	#pull info from registration page
	username = request.form['username']
	password = request.form['password']

	cursor = conn.cursor()
	#Check for existance of new user
	query = 'SELECT * FROM Person WHERE username = %s'
	cursor.execute(query, (username))
	print ("existence check complete")
	data = cursor.fetchone()
	err = None
	if(data):
		error = "This user already exists"
		return render_template('register.html', error = err)
	else:
		ins = 'INSERT INTO Person (username,password) VALUES(%s, sha1(%s))'
		cursor.execute(ins, (username, password))
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
	query = 'SELECT * FROM Person WHERE username = %s and password = sha1(%s)'
	cursor.execute(query, (username, password))
	data = cursor.fetchone()
	cursor.close()
	error = None
	if(data):
		#creates a session for the the user
		session['username'] = username
		return redirect(url_for('home'))
	else:
		#returns an error message to the html page
		error = 'Invalid login or username'
		return render_template('login.html', error=error)

app.secret_key = 'some key that you will never guess'

if __name__ == "__main__":
		app.run()



