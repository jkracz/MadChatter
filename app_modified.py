from flask import Flask, render_template, request, redirect, session, url_for
import pymysql.cursors
from hashlib import sha1
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
import django

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

@app.route("/register")
def register():
	return render_template('register.html')

@app.route("/home.html")
def home():
	username = session['username']
	cursor = conn.cursor();
	query = 'SELECT timest,file_path,content_name FROM Content WHERE username = %s OR public = 1 ORDER BY timest DESC'
	cursor.execute(query, (username))
	data = cursor.fetchall()
	cursor.close()
	return render_template('home.html', username=username, posts=data)

#Register new user 
class Register(regform):
        firstName = StringField('First name', [validators.Length(min = 1, max = 50)])
        lastName = StringField('Last name', [validators.Length(min= 1, max = 50)])
        username = StringField('Username', [validators.DataRequired(), validators.Length(min = 5, max = 20)])
        email= StringField('Email Address', [validators.Length(min = 5, max = 30)])
        passWord = PasswordField('Password', [validators.DataRequired(),
                                              validators.EqualTo('confirmPW', message='Passwords do not match'),
                                              validators.Length(min = 5, max = 12)])
        confirmPW = PasswordField('Confirm your password')
        
def dupUser(username):
        cursor = conn.cursor()
        query = 'SELECT username FROM person WHERE username == %s' % username
        cursor.execute(query)
        data = cursor.fetchone()
        if data == 'None':
                return 1
        else:
                return 0
@app.route('/registerAuth', methods=['GET', 'POST'])
#check in database for dup username

        
def registerAuth():
        form = Register(request.form)
        if request.method == 'POST' and form.validate():
                return render_template('register.html', form=form)
        
        

#log in user
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
	#grabs information from the forms

	username = request.form['username']
	password = request.form['password']

	#retrieves username and password
	cursor = conn.cursor()
	query = 'SELECT password FROM Person WHERE username = %s AND password = sha1(%s)'
	cursor.execute(query, (username, password.encode()))
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

@app.route('/logout')
def logout():
	session.pop('username')
	return redirect('/')
#resetPassword
@app.route('/resetPassword', methods=['POST'])
def resetPassword():
	return redirect('/')


@app.route('/post', methods=['GET', 'POST'])
def post():
	username = session['username']
	cursor = conn.cursor();
	content = request.form['content']
	description = request.form['description']
	public = request.form['makePublic']
	if(public != '1'):
		public = '0'
	query = 'INSERT INTO Content (username,file_path,content_name,public) VALUES(%s, %s, %s, %s)'
	cursor.execute(query, (username,content,description,public))
	conn.commit()
	cursor.close()
	return redirect(url_for('home'))
def comment():
        username = session['username']
        cursor = conn.cursor();
        comment = request.form['Comment']
        


app.secret_key = 'some key that you will never guess'

if __name__ == "__main__":
		app.run(debug=True)



