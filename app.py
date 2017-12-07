#still need a random password generator for password reset
from flask import Flask, render_template, request, redirect, session, url_for
import pymysql.cursors
from hashlib import sha1
from functools import wraps
from socket import *
from datetime import datetime
import email_module as em

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
    
#log in user
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
	#grabs information from the forms

	username = request.form['username']
	password = request.form['password']

	#retrieves username and password
	boo_value = check_user_pw(username, password)
	
	if(boo_value):
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
            ##need to implement error message
            return redirect(url_for('login'))
        else:
            return rediret(url_for('login'))
    return render_template('change_password.html')

            
@app.route('/forgot_password')
def forgot_password():
    return render_template('reset_password.html')

@app.route('/reset_password', methods = ['GET', 'POST'])
def reset_password():
    username = request.form['username']
    email = request.form['email']
    checkAccount(username, email)
    return redirect(url_for('login'))

@app.route('/create_group', methods = ['GET', 'POST'])
def create_group():
    if request.method == 'POST':
        username = session['username']
        group_name = request.form['group_name']
        description = request.form['description']
        check_query = "SELECT * FROM friendgroup WHERE username = %s AND group_name = %s"
        cursor = conn.cursor()
        cursor.execute(check_query, (username, group_name))
        already_exists = cursor.fetchone()
        if already_exists:
            error = 'This group already exists'
            return render_template('friend_group.html', error = error)
        else:
            insert_query = 'INSERT INTO friendgroup VALUES (%s, %s, %s)'
            cursor.execute(insert_query, (group_name, username, description))
            conn.commit()
            cursor.close()
            message = 'You have successfully created your friendgroup: %s' % group_name
            return render_template('friend_group.html', message = message)
    return render_template('create_group.html')
        
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
                message = "Your temporary password is: %s" % new_pw
                em.send_email(message, email)      
        #if account doesn't exist, return 0
        else:
                return 'failed'
            
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
    
@app.route('/friend_group', methods = ['GET'])
def friend_group():
    if request.method == 'GET':
        username = session['username']
        cursor = conn.cursor()
        get_friend_group = "SELECT group_name FROM friendgroup WHERE username = %s"
        cursor.execute(get_friend_group, (username))
        data = cursor.fetchall()
        cursor.close()
        if data:
            return render_template('friend_group.html', group_list = data)
        else:
            message = "You don't have any friend groups"
            return render_template('friend_group.html', message = message)
    
    
    
@app.route('/add_friend/<group_name>', methods = ['GET', 'POST'])
def add_friend(group_name):
    if request.method == 'POST':
        target_username = request.form['target_username']
        target_group_name = group_name
        username = session['username']
        user_exist = search_user(target_username)
        if user_exist:
            inst = "INSERT INTO member VALUES (%s, %s, %s)"
            cursor = conn.cursor()
            cursor.execute(inst, (target_username, target_group_name, username))
            conn.commit()
            cursor.close()
            message = 'You have successfully added %s to your group: %s' % (target_username, target_group_name)
            return render_template('friend_group.html', message = message)
        else:
            error = "User cannot be found"
            return render_template('friend_group.html', error = error)
    return render_template('add_friend.html', group_name = group_name)
    
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
    
@app.route('/share_via_email/<item_id>', methods = ['GET', 'POST'])
def share_via_email(item_id):
    if request.method == 'POST':
        
        target_group = request.form['target_group']
        content_shared = item_id
        username = session['username']
        
        #check if friend group exists
        cursor = conn.cursor()
        check_query = "SELECT * from friendgroup WHERE username = %s AND friendgroup.group_name = %s"
        cursor.execute(check_query, (username, target_group))
        group_valid = cursor.fetchone()
        #if group exists
        if group_valid:
            insert_query = "INSERT INTO share VALUES (%s, %s, %s)"
            cursor.execute(insert_query, (content_shared, target_group, username))
            conn.commit()
            #get list of member emails
            find_member_email = "SELECT email FROM member NATURAL JOIN person WHERE member.group_name = %s AND member.username_creator = %s"
            cursor.execute(find_member_email, (target_group, session['username']))
            email_list = cursor.fetchall()
            message = "%s has shared the following item: %s with you" % (session['username'], item_id)
            #send emails 
            for email in email_list:
                em.send_email(message, email)
            return render_template('home.html', message = message)
    error = 'We had some problem with sharing, please try again'
    return render_template('home.html', message = error)
            
            
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
        #data
        content_id = request.form['content_id']
        comment = request.form['comment']
        username = session['username']
        #time stamp
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

@app.route('/profile') #MUST IMPLEMENT NOT MY profiles
@login_required
def profile():
    return render_template('profile.html')


@app.route('/myProfile')
def myProfile():
	username = session['username']
	cur = conn.cursor();
	friendsQuery = 'SELECT m.username, p.first_name, p.last_name FROM Member AS m\
									JOIN Person AS p ON (m.username = p.username)\
									WHERE (group_name,username_creator) IN (SELECT group_name,username_creator\
											                                     FROM Member\
											                                     WHERE username = %s)'
	cur.execute(friendsQuery, (username))
	friendsList = cur.fetchall()
	cur.close()
	return render_template('profile.html', user=username,friends=friendsList)


@app.route('/notif') #MUST IMPLEMENT
@login_required
def notif():
    return render_template('notif.html')


@app.route('/home_nav') #MAY NEED TO IMPLEMENT, NOT SURE
def home_nav():
    return redirect(url_for('home'))


app.secret_key = 'some key that you will never guess'

if __name__ == "__main__":
    app.run(debug=True)


