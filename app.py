from flask import Flask, render_template, request, redirect, session, url_for
import pymysql.cursors
from hashlib import sha1
from functools import wraps
from socket import *
from datetime import datetime
import email_module as email

app = Flask(__name__)

#Connect to MadChatter DB
conn = pymysql.connect(host='localhost',
	port=3306,
	user='root',
	password='',
	db='MadChatter',
	charset='utf8mb4',
	cursorclass=pymysql.cursors.DictCursor)

#wrap around functions that are only available to logged in users
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            return redirect(url_for('login'))
    return wrap

@app.route("/")
def main():
	return render_template('index.html')

@app.route("/login")
def login():
    #if 'logged_in' in session:
        #return redirect(url_for('home'))
    return render_template('login.html')

@app.route("/register")
def register():
	return render_template('register.html')

@app.route("/home")
@login_required
def home():
	username = session['username']
	cursor = conn.cursor();
	query = 'SELECT id, timest, file_path, content_name FROM content WHERE username = %s OR public = 1 ORDER BY timest DESC'
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
                #session['logged_in'] tracks if user =logged in
		session['username'] = username
		session['logged_in'] = True
		return redirect(url_for('home'))
	else:
		#returns an error message to the html page
		error = 'Invalid login or username'
		return render_template('login.html', error=error)


@app.route('/resetPassword', methods=['POST'])
def resetPassword():
	##incomplete
        return redirect('reset_password.html')


#when user resets password, function checks for associated account and mail password
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
                email.mailPassword(new_pw, email)
                return 'Password reset was successful, new password has been mailed to your email!'
        #if account doesn't exist, return 0
        else:
                return 'User cannot be found'

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
	conn.commit()
	cursor.close()
	return redirect(url_for('home'))

@app.route('/view/<int:item_id>/', methods=['GET'])
@login_required
def view(item_id):
        inst = "SELECT * FROM content WHERE content.id = %s"
        cursor = conn.cursor();
        cursor.execute(inst, (item_id))
        data = cursor.fetchall()
        cursor.close()
        return render_template('view.html', view_item = data)

@app.route('/comment/<int:item_id>', methods=['GET', 'POST'])
@login_required
def comment(item_id):
    return render_template('comment.html', content_id = item_id)

@app.route('/post_comment', methods=['POST'])
def post_comment():
    if request.method == 'POST':
        content_id = request.form['content_id']
        comment = request.form['comment']
        username = session['username']
        time = str(datetime.now())

        inst = "INSERT INTO comment(id, username, timest, comment_text) VALUES (%s, %s, %s, %s)"
        cursor = conn.cursor();
        cursor.execute(inst, (content_id, username, time, comment))
        conn.commit()
        cursor.close()
        return redirect(url_for('home'))

@app.route('/logout')
@login_required
def logout():
	session.pop('username')
	session.clear()
	return redirect('/')


@app.route('/profile/<username>')
def profile(username):
	cur = conn.cursor();
	friendsQuery = 'SELECT m.username, p.first_name, p.last_name FROM Member AS m\
									JOIN Person AS p ON (m.username = p.username)\
									WHERE (group_name,username_creator) IN (SELECT group_name,username_creator\
											                                     FROM Member\
											                                     WHERE username = %s)'
	cur.execute(friendsQuery, (username))
	friendsList = cur.fetchall()
	groupQuery = 'SELECT group_name,\
								CASE\
									WHEN username_creator = %s THEN "Owner"\
									ELSE "Member"\
								END AS status\
								FROM Member\
								WHERE username = %s'
	cur.execute(groupQuery, (username,username))
	groupList = cur.fetchall()
	postQuery = 'SELECT * FROM Content WHERE username = %s ORDER BY timest DESC'
	cur.execute(postQuery, (username))
	userPosts = cur.fetchall()
	personInfoQuery = 'SELECT first_name, last_name FROM Person WHERE username=%s'
	cur.execute(personInfoQuery, (username))
	personInfo = cur.fetchall()
	cur.close()
	return render_template('profile.html', username=username, user=personInfo, friends=friendsList, groups=groupList, posts=userPosts)

@app.route('/tag/<int:item_id>', methods=['POST'])
def tag(item_id):
	tagger = session['username']
	taggee = request.form['taggee']
	addTag = 'INSERT INTO Tag (id,username_tagger,username_taggee) VALUES (%s, %s, %s)'
	cur = conn.cursor();
	cur.execute(addTag, (item_id,tagger,taggee))
	conn.commit()
	cur.close()
	return redirect(url_for('home'))

@app.route('/acceptTag/<int:item_id>', methods=['POST'])
def acceptTag(item_id):
	username = session['username']
	acceptQuery = 'UPDATE Tag SET status = 1 WHERE id = %s AND username_taggee = %s AND status = 0'
	cur = conn.cursor()
	cur.execute(acceptQuery, (item_id,username))
	conn.commit()
	cur.close()
	return redirect(url_for('notif'))

@app.route('/denyTag/<int:item_id>', methods=['POST'])
def denyTag(item_id):
	username = session['username']
	denyQuery = 'DELETE FROM Tag WHERE id = %s AND username_taggee = %s AND status = 0'
	cur = conn.cursor()
	cur.execute(denyQuery, (item_id,username))
	conn.commit()
	cur.close()
	return redirect(url_for('notif'))

@app.route('/notif') #MUST IMPLEMENT
@login_required
def notif():
<<<<<<< HEAD
    return render_template('notif.html', username=session['username'])
=======
	username = session['username']
	tagsQuery = 'SELECT t.id, file_path, username_tagger FROM Content AS c\
								JOIN Tag AS t ON (c.id = t.id) WHERE username_taggee=%s AND status = 0 ORDER BY t.timest DESC'
	cur = conn.cursor()
	cur.execute(tagsQuery, (username))
	pendingTags = cur.fetchall()
	cur.close()
	return render_template('notif.html', username=username,pendingTags=pendingTags)
>>>>>>> 2512cab2edd7cc4a06de5e8269004b9b93149456


app.secret_key = 'some key that you will never guess'

if __name__ == "__main__":
		app.run(debug=True)


