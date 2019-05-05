from flask import Flask, request, make_response, render_template, redirect
import sqlite3
import secrets
import hashlib
import re

app = Flask(__name__)

def createSessionAuthenticated(userName):
	h = hashlib.sha512()
	h.update(str.encode(userName))
	sid = h.hexdigest()

	db = sqlite3.connect("data.sqlite3")
	c = db.cursor()
	c.execute("INSERT OR REPLACE INTO sessions VALUES (:sid, (SELECT datetime('now','+1 hour')), :userName);", {"sid": sid, "userName": userName})
	db.commit()
	db.close()

	return (sid, 3600)

def removeSession(sessionID):
	db = sqlite3.connect("data.sqlite3")
	c = db.cursor()
	c.execute("DELETE FROM sessions WHERE sessionID = :sid;", {"sid": sessionID})
	db.commit()
	db.close()

	return ("", 0)

def removeSessionsExpired():
	db = sqlite3.connect("data.sqlite3")
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

	db = sqlite3.connect("data.sqlite3")
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

	db = sqlite3.connect("data.sqlite3")
	c = db.cursor()
	c.execute("SELECT sessionID, expiresAfter, userName FROM sessions WHERE sessionID = :sid;", {"sid": sessionCookie})
	session = c.fetchone()
	db.close()

	return session

def auth(userName, password):
	db = sqlite3.connect("data.sqlite3")
	c = db.cursor()
	c.execute("SELECT salt, hash FROM users WHERE userName = :userName;", {"userName": userName})
	r = c.fetchone()
	db.close()

	if r == None:
		return False # unknown user name

	h = hashlib.sha512()
	h.update(str.encode(r[0])) # salt
	h.update(str.encode(password))
	hash = h.hexdigest()

	return r[1] == hash

def login(userName, password):
	if auth(userName, password):
		return createSessionAuthenticated(userName)
	return None

def initDB():
	db = sqlite3.connect("data.sqlite3")
	c = db.cursor()
	c.execute("CREATE TABLE IF NOT EXISTS sessions (sessionID TEXT NOT NULL UNIQUE, expiresAfter TEXT NOT NULL, userName TEXT NOT NULL, PRIMARY KEY(sessionID));")
	c.execute("CREATE TABLE IF NOT EXISTS users (userName TEXT NOT NULL UNIQUE, salt TEXT NOT NULL, hash TEXT NOT NULL, PRIMARY KEY(userName));")
	db.commit()
	db.close()

def validUserName(userName):
	# a valid user name may contain only alphanumeric characters
	# and must be at least 4 and at most 32 characters long
	return not re.match(r"^[a-zA-Z0-9]{4,32}$", userName) == None

def validPassword(password):
	# a valid password may contain only alphanumeric characters or underscores
	# and must be at least 4 and at most 32 characters long
	return not re.match(r"^[a-zA-Z0-9_]{4,32}$", password) == None

@app.route("/index.html")
def pageIndex():
	session = getSession(request)

	if session == None:
		return render_template("index.html")

	return render_template("index.html", session = session, userName = session[2])

@app.route("/login.html", methods=['GET', 'POST'])
def pageLogin():
	# redirect if user is already logged in
	if not getSession(request) == None:
		return redirect("index.html")

	if request.method == "POST":
		try:
			userProvided = request.form["user"]
			passwordProvided = request.form["password"]
		except KeyError:
			abort(400)

		if not validUserName(userProvided) or not validPassword(passwordProvided):
			return render_template("login.html", msg = "Wrong username / password")

		result = login(userProvided, passwordProvided)
		if result == None:
			return render_template("login.html", msg = "Wrong username / password", user = userProvided)

		# redirect on successful login
		response = redirect("index.html")
		response.set_cookie(key = "session", value = result[0],
				max_age = result[1]);
		return response
	else:
		return render_template("login.html")

@app.route("/logout.html", methods=['POST'])
def pageLogout():
	session = getSession(request)

	# redirect if user is not logged in
	if session == None:
		return redirect("index.html")

	result = removeSession(session[0])

	# redirect on successful logout
	response = redirect("index.html")
	response.set_cookie(key = "session", value = result[0],
			max_age = result[1]);
	return response

@app.route("/register.html", methods=['GET', 'POST'])
def pageRegister():
	# redirect if user is already logged in
	if not getSession(request) == None:
		return redirect("index.html")

	if request.method == "POST":
		try:
			userProvided = request.form["user"]
			passwordProvided = request.form["password"]
		except KeyError:
			abort(400)

		if not validUserName(userProvided) or not validPassword(passwordProvided):
			return render_template("register.html", msg = "Illegal input")

		if not createUser(userProvided, passwordProvided):
			return render_template("register.html", msg = "Username already exists", user = userProvided)

		# login once user is created
		result = login(userProvided, passwordProvided)

		response = redirect("index.html")
		response.set_cookie(key = "session", value = result[0],
				max_age = result[1]);
		return response
	else:
		return render_template("register.html")

initDB()
