from flask import Flask, render_template, request, redirect, session, url_for
import pymysql.cursors
from hashlib import sha1
from functools import wraps
from socket import *
from datetime import datetime
import email_module as em
import random
import string

app = Flask(__name__)

#Connect to MadChatter DB
conn = pymysql.connect(host='localhost',
	port=8889,
	user='root',
	password='root',
	db='MadChatter',
	charset='utf8mb4',
	cursorclass=pymysql.cursors.DictCursor)

#function determines if target username exists
def search_user(target_username):
    cursor = conn.cursor()
    inst = "SELECT * FROM person WHERE username = %s"
    cursor.execute(inst, (target_username))
    exist = cursor.fetchone()
    cursor.close()
    if exist:
        return True
    else:
        return False

#function checks username and password if they match and return boolean value
def check_user_pw(username, password):
    cursor = conn.cursor()
    inst = "SELECT * FROM person WHERE username = %s AND password = sha(%s)"
    cursor.execute(inst, (username, password))
    valid = cursor.fetchone()
    cursor.close()
    if valid:
        return True
    else:
        return False
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
    message = False
    if (session.get('logged_in') == True):
            message = True
    return render_template('index.html',message=message)

@app.route("/login")
def login():
    message = False
    if (session.get('logged_in') == True):
            message = True
    return render_template('login.html')

@app.route("/register")
def register():
	return render_template('register.html')

@app.route("/home")
@login_required
def home():
	username = session['username']
	cursor = conn.cursor();
	postQuery = 'SELECT id, timest, file_path, content_name, first_name, last_name FROM content NATURAL JOIN person\
								WHERE username = %s\
								OR public = 1\
								OR username IN (SELECT DISTINCT m.username FROM Member AS m\
																WHERE (group_name,username_creator) IN (SELECT group_name,username_creator\
											                                     							FROM Member\
											                                     							WHERE username = %s))\
								OR id IN (SELECT id FROM Share AS s\
													JOIN Member AS m ON (s.group_name = m.group_name AND s.username = m.username_creator)\
													WHERE m.username=%s)\
								ORDER BY timest'
	cursor.execute(postQuery, (username,username,username))
	postData = cursor.fetchall()
	userQuery = 'SELECT first_name FROM Person WHERE username=%s'
	cursor.execute(userQuery, (username))
	userData = cursor.fetchone()
	cursor.close()
	return render_template('home.html', username=username, user=userData, posts=postData)

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
		return render_template('register.html', error = True)
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


@app.route('/change_password', methods = ['GET','POST'])
def change_password():
    if request.method == 'POST':
        username = session['username']
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        if (check_user_pw(username, current_password) and (new_password == confirm_password)):
            cursor = conn.cursor()
            inst = ("UPDATE person SET password = sha1(%s) WHERE username = %s")
            cursor.execute(inst, (new_password, username))
            conn.commit()
            cursor.close()
            return redirect(url_for('home'))
        elif (new_password != confirm_password):
            return render_template('change_password.html', username=session['username'], passNoMatch=True)
        else:
            return render_template('change_password.html', username=session['username'], incorrectPass=True)
    return render_template('change_password.html', username=session['username'])


@app.route('/forgot_password')
def forgot_password():
    return render_template('reset_password.html')

@app.route('/reset_password', methods = ['GET', 'POST'])
def reset_password():
    username = request.form['username']
    email = request.form['email']
    checkAccount(username, email)
    return redirect(url_for('login'))


@app.route('/delete/<item_id>', methods = ['GET', 'POST'])
def delete(item_id):
    username = session['username']
    delete_query = "DELETE FROM content WHERE username = %s AND content.id = %s"
    cursor = conn.cursor()
    cursor.execute(delete_query, (username, item_id))
    conn.commit()
    cursor.close()
    message = "Item has been deleted"
    return redirect(url_for('profile',username=username))


@app.route('/create_group', methods = ['GET', 'POST'])
def create_group():
    username = session['username']
    if request.method == 'POST':
        group_name = request.form['group_name']
        description = request.form['description']
        check_query = "SELECT * FROM friendgroup WHERE username = %s AND group_name = %s"
        cursor = conn.cursor()
        cursor.execute(check_query, (username, group_name))
        already_exists = cursor.fetchone()
        if already_exists:
            return render_template('error.html', error = "groupExists", username=username)
        else:
            insert_query = 'INSERT INTO friendgroup VALUES (%s, %s, %s)'
            memberInsert = 'INSERT INTO Member (username,group_name,username_creator) VALUES (%s,%s,%s)'
            cursor.execute(insert_query, (group_name, username, description))
            cursor.execute(memberInsert, (username,group_name,username))
            conn.commit()
            cursor.close()
            message = 'You have successfully created your friendgroup: %s' % group_name
            return redirect(url_for('profile', username = username))
    return render_template('create_group.html', username=username)

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
                new_pw = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                inst = 'UPDATE person SET password = sha1(%s) WHERE username = %s AND email = %s'
                cursor = conn.cursor()
                cursor.execute(inst, (new_pw, username, email))
                conn.commit()
                cursor.close()
                message = "Your temporary password is: %s" % new_pw
                em.send_email(message, email)
        #if account doesn't exist, return 0
        else:
                return 'failed'

@app.route('/emailShare/<item_id>', methods = ['GET', 'POST'])
def emailShare(item_id):
    target_username = request.form['share_to']
    user_exist = search_user(target_username)
    if user_exist:



        ##get email

        inst = "SELECT email FROM person WHERE username = %s"
        cursor = conn.cursor()
        cursor.execute(inst, (target_username))
        data = cursor.fetchone()
        email = data['email']
        cursor.close()

        ##get filepath
        get_filepath = "SELECT file_path FROM content WHERE content.id = %s"
        cursor = conn.cursor()
        cursor.execute(get_filepath, (item_id))
        file_data = cursor.fetchone()
        cursor.close()
        file_path = file_data['file_path']
        ##current user
        username = session['username']

        composed_message = "%s shared the following item with you!\nLink:%s"  % (username, file_path)
        em.send_email(composed_message, email)
        message = "You have shared %s with %s" % (item_id, target_username)
        return redirect(url_for('home'))
    elif user_exist == False:
        return render_template('error.html', error="usernotfound", username=username)
    else:
        return render_template('error.html', error="generror", username=username)

@app.route('/share/<item_id>', methods=['GET','POST'])
def share(item_id):
	group = request.form['gname']
	owner = request.form['owner']
	check = 'SELECT * FROM Member WHERE group_name = %s AND username_creator = %s AND username = %s'
	cur = conn.cursor()
	cur.execute(check, (group,owner,session['username']))
	exist = cur.fetchone()
	if (exist):
		insert_query = 'INSERT INTO Share (id,group_name,username) VALUES (%s,%s,%s)'
		cur.execute(insert_query, (item_id,group,owner))
		conn.commit()
		cur.close()
		return redirect(url_for('home'))
	else:
		cur.close()
		return render_template('error.html', error="share", username=session['username'])

@app.route('/post', methods=['GET', 'POST'])
@login_required
def post():
	username = session['username']
	cursor = conn.cursor();
	content = request.form['content']
	description = request.form['description']
	public = '0'
	if(request.form.get('makePublic')):
		public = '1'
	query = 'INSERT INTO content (username,file_path,content_name,public) VALUES(%s, %s, %s, %s)'
	cursor.execute(query, (username,content,description,public))
	conn.commit()
	cursor.close()
	return redirect(url_for('home'))

@app.route('/add_friend/<group_name>', methods = ['GET', 'POST'])
def add_friend(group_name):
    if request.method == 'POST':
        target_username = request.form['target_username']
        target_group_name = group_name
        username = session['username']

        user_exist = search_user(target_username)
        if (user_exist):
            cursor = conn.cursor()
            alreadyMember = 'SELECT * FROM Member WHERE username=%s AND username_creator=%s AND group_name=%s'
            cursor.execute(alreadyMember, (target_username,username,target_group_name))
            if (cursor.fetchone()):
                    cursor.close()
                    return render_template('error.html', error="alreadymember", username=username)
            else:
                    inst = "INSERT INTO member VALUES (%s, %s, %s)"
                    cursor.execute(inst, (target_username, target_group_name, username))
                    conn.commit()
                    cursor.close()
                    return redirect(url_for('profile', username = username))
        else:
            return render_template('error.html', error="usernotfound", username=username)

def get_comments(item_id):
    inst = "SELECT comment_text, timest, first_name, last_name FROM (SELECT id, username, comment_text, timest, first_name, last_name FROM comment NATURAL JOIN person WHERE comment.username=person.username) as t1 WHERE id = %s ORDER BY timest"
    cursor = conn.cursor()
    cursor.execute(inst, (item_id))
    comments = cursor.fetchall()
    cursor.close()
    return comments

def get_tags(item_id):
    inst = "SELECT username_taggee, username_tagger FROM tag WHERE tag.id = %s AND status=1"
    cursor = conn.cursor()
    cursor.execute(inst, (item_id))
    tags = cursor.fetchall()
    cursor.close()
    return tags

@app.route('/view/<item_id>/', methods=['GET'])
@login_required
def view(item_id):
    username=session['username']
    inst = "SELECT id, file_path, content_name, timest, first_name, last_name FROM (SELECT first_name, last_name, id, file_path, content_name, timest FROM Person NATURAL JOIN Content WHERE Person.username=Content.username) as t1 WHERE id = %s"
    cursor = conn.cursor()
    cursor.execute(inst, (item_id))
    content = cursor.fetchone()
    comments = get_comments(item_id)
    tags = get_tags(item_id)
    cursor.close()
    return render_template('view.html', username=username, content = content, comments = comments, tags = tags)



@app.route('/comment/<int:item_id>', methods=['GET', 'POST'])
@login_required
def comment(item_id):
    comment = request.form['comment']
    username = session['username']
    time = str(datetime.now())
    inst = "INSERT INTO comment(id, username, timest, comment_text) VALUES (%s, %s, %s, %s)"
    cursor = conn.cursor();
    cursor.execute(inst, (item_id, username, time, comment))
    conn.commit()
    cursor.close()
    return redirect(url_for('view', item_id = item_id))


@app.route('/logout')
@login_required
def logout():
	session.pop('username')
	session.clear()
	return redirect('/')


@app.route('/profile/<username>')
def profile(username):
	cur = conn.cursor();
	friendsQuery = 'SELECT DISTINCT m.username, p.first_name, p.last_name FROM Member AS m\
									JOIN Person AS p ON (m.username = p.username)\
									WHERE (group_name,username_creator) IN (SELECT group_name,username_creator\
											                                     FROM Member\
											                                     WHERE username = %s)\
									AND m.username <> %s'
	cur.execute(friendsQuery, (username, username))
	friendsList = cur.fetchall()
	groupQuery = 'SELECT * FROM Member WHERE username = %s'
	cur.execute(groupQuery, (username))
	groupList = cur.fetchall()
	postQuery = 'SELECT * FROM Content WHERE username = %s ORDER BY timest'
	cur.execute(postQuery, (username))
	userPosts = cur.fetchall()
	personInfoQuery = 'SELECT first_name, last_name FROM Person WHERE username=%s'
	cur.execute(personInfoQuery, (username))
	personInfo = cur.fetchone()
	cur.close()
	return render_template('profile.html', username=username, user=personInfo, friends=friendsList, groups=groupList, posts=userPosts)

@app.route('/tag/<int:item_id>', methods=['POST'])
def tag(item_id):
	tagger = session['username']
	taggee = request.form['taggee']
	cur = conn.cursor()
	if (search_user(taggee)):
		tagged = 'SELECT * FROM Tag WHERE id=%s AND username_taggee=%s'
		cur.execute(tagged, (item_id,taggee))
		isTagged = cur.fetchone()
		if (isTagged):
			cur.close()
			return render_template('error.html', error="alreadytagged", username=tagger)
		else:
			addTag = 'INSERT INTO Tag (id,username_tagger,username_taggee) VALUES (%s, %s, %s)'
			cur.execute(addTag, (item_id,tagger,taggee))
			conn.commit()
			cur.close()
			return redirect(url_for('home'))
	else:
		cur.close()
		return render_template('error.html', error="usernotfound", username=tagger)

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

@app.route('/notif')
@login_required
def notif():
	username = session['username']
	tagsQuery = 'SELECT t.id, file_path, username_tagger, content_name FROM Content AS c\
								JOIN Tag AS t ON (c.id = t.id) WHERE username_taggee=%s AND status = 0 ORDER BY t.timest DESC'
	cur = conn.cursor()
	cur.execute(tagsQuery, (username))
	pendingTags = cur.fetchall()
	cur.close()
	return render_template('notif.html', username=username,pendingTags=pendingTags)


app.secret_key = 'some key that you will never guess'

if __name__ == "__main__":
		app.run(debug=True)


