from flask import Flask, request, make_response
import datetime
import sqlite3
import secrets
import hashlib

app = Flask(__name__)

def createSessionAuthenticated(userName):
	h = hashlib.sha512()
	h.update(str.encode(userName))
	sid = h.hexdigest()

	db = sqlite3.connect("session_data.sqlite3")
	c = db.cursor()
	c.execute("INSERT OR REPLACE INTO sessions VALUES (:sid, (SELECT datetime('now','+1 hour')), :userName);", {"sid": sid, "userName": userName})
	db.commit()
	db.close()

	return (sid, 3600)

def removeSession(sessionID):
	db = sqlite3.connect("session_data.sqlite3")
	c = db.cursor()
	c.execute("DELETE FROM sessions WHERE sessionID = :sid;", {"sid": sessionID})
	db.commit()
	db.close()

	return ("", 0)

def removeSessionsExpired():
	db = sqlite3.connect("session_data.sqlite3")
	c = db.cursor()
	c.execute("DELETE FROM sessions WHERE expiresAfter < (SELECT datetime('now'));")
	db.commit()
	db.close()

def createUser(userName, password):
	salt = secrets.token_hex(32)

	h = hashlib.sha512()
	h.update(str.encode(salt))
	h.update(str.encode(password))
	hash = h.hexdigest()

	db = sqlite3.connect("session_data.sqlite3")
	c = db.cursor()
	try:
		c.execute("INSERT INTO users VALUES (:userName, :salt, :hash);", {"userName": userName, "salt": salt, "hash": hash})
	except sqlite3.IntegrityError: # username already exists
		db.close()
		return False

	db.commit()
	db.close()
	return True

def getSession(request):
	sessionCookie = request.cookies.get("session")
	if sessionCookie == None:
		return None

	db = sqlite3.connect("session_data.sqlite3")
	c = db.cursor()
	c.execute("SELECT sessionID, expiresAfter, userName FROM sessions WHERE sessionID = :sid;", {"sid": sessionCookie})
	session = c.fetchone()
	db.close()

	return session

def login(request, userName, password):
	db = sqlite3.connect("session_data.sqlite3")
	c = db.cursor()
	c.execute("SELECT salt, hash FROM users WHERE userName = :userName;", {"userName": userName})
	r = c.fetchone()
	db.close()

	if r == None:
		return None # unknown user name

	salt = r[0]
	hashDB = r[1]

	h = hashlib.sha512()
	h.update(str.encode(salt))
	h.update(str.encode(password))
	hash = h.hexdigest()

	if hashDB == hash:
		# invalidate any old session
		session = getSession(request)
		if session != None:
			removeSession(session[0])

		return createSessionAuthenticated(userName)
	else:
		return None # wrong username / password

def initDB():
	db = sqlite3.connect("session_data.sqlite3")
	c = db.cursor()
	c.execute("CREATE TABLE IF NOT EXISTS sessions (sessionID TEXT NOT NULL UNIQUE, expiresAfter TEXT NOT NULL, userName TEXT NOT NULL, PRIMARY KEY(sessionID));")
	c.execute("CREATE TABLE IF NOT EXISTS users (userName TEXT NOT NULL UNIQUE, salt TEXT NOT NULL, hash TEXT NOT NULL, PRIMARY KEY(userName));")
	db.commit()
	db.close()

@app.route("/python")
def pageIndex():
	session = getSession(request)

	if session == None:
		return "<h3>Whupp whupp! Not logged in.</h3>"

	return "<h3>Whupp whupp! Logged in as: {}</h3>".format(session[2])

@app.route("/python/login")
def pageLogin():
	result = login(request, "testUserName", "testPassword")

	if result == None:
		return "<h3>Wrong username / password</h3>"

	response = make_response("<h3>Logging in...</h3>")
	response.set_cookie(key = "session", value = result[0],
			max_age = result[1], httponly = True);
	return response

@app.route("/python/logout")
def pageLogout():
	session = getSession(request)

	if session == None:
		return "<h3>Whupp whupp! Not logged in.</h3>"

	result = removeSession(session[0])

	response = make_response("<h3>Whupp whupp! Logged out.</h3>")
	response.set_cookie(key = "session", value = result[0],
			max_age = result[1], httponly = True);
	return response

@app.route("/python/register")
def pageRegister():
	result = createUser("testUserName", "testPassword")

	if result == False:
		return "<h3>Username already exists.</h3>"

	return "<h3>Account created</h3>"

@app.route('/python/db')
def pageDEBUGDB():
	db = sqlite3.connect("session_data.sqlite3")
	c = db.cursor()
	c.execute("SELECT * FROM sessions;")
	sessions = c.fetchall()
	c.execute("SELECT * FROM users;")
	users = c.fetchall()
	db.close()

	result = ""

	result += "<h3>Sessions</h3>"
	for session in sessions:
		result += "SessionID " + session[0] + " expiresAfter " + session[1] + " User " + session[2] + "<br />"

	result += "<h3>Users</h3>"
	for user in users:
		result += "Username " + user[0] + " Salt " + user[1] + " Hash " + user[2] + "<br />"

	return result

initDB()
