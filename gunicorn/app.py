from flask import Flask, request, make_response
import datetime
import sqlite3
import secrets

app = Flask(__name__)

def getSession(request):
	sessionCookie = request.cookies.get("session")
	if sessionCookie == None:
		return None

	sessionDB = sqlite3.connect("session_data.sqlite3")
	c = sessionDB.cursor()
	c.execute("SELECT * FROM sessions WHERE sessionID = :sid;", {"sid": sessionCookie})
	session = c.fetchone()
	sessionDB.close()

	return session

def newSession(response, userID = None):
	sid = secrets.token_hex(32)

	response.set_cookie(key = "session", value = sid,
			max_age = 3600, httponly = True
		);

	sessionDB = sqlite3.connect("session_data.sqlite3")
	c = sessionDB.cursor()
	c.execute("INSERT INTO sessions VALUES (:sid, :max_age, :uid);", {"sid": sid, "max_age": 3600, "uid": userID})
	sessionDB.commit()
	sessionDB.close()

	return (sid, 3600, userID)

def login(request, response, userID):
	session = getSession(request)
	if session != None:
		return

	return newSession(response, userID)

def logout(request, response):
	session = getSession(request)
	if session == None:
		return

	# remove cookie
	response.set_cookie(key = "session", value = "",
			max_age = 0, httponly = True
		);

	sessionDB = sqlite3.connect("session_data.sqlite3")
	c = sessionDB.cursor()
	c.execute("DELETE FROM sessions WHERE sessionID = :sid;", {"sid": session[0]})
	sessionDB.commit()
	sessionDB.close()

def initSessionDB():
	sessionDB = sqlite3.connect("session_data.sqlite3")
	c = sessionDB.cursor()
	c.execute("CREATE TABLE IF NOT EXISTS sessions (sessionID TEXT NOT NULL UNIQUE, expiresIn INTEGER, userID INTEGER, PRIMARY KEY(sessionID));")
	c.execute("CREATE TABLE IF NOT EXISTS users (userID INTEGER NOT NULL UNIQUE, userName TEXT, PRIMARY KEY(userID));")
	sessionDB.commit()
	sessionDB.close()

@app.route("/python")
def hello():
	session = getSession(request)

	if session == None:
		response = make_response("<h3>Whupp whupp! New Session</h3>")
		newSession(response)

		return response

	return "<h3>Whupp whupp! SessionID: {}</h3>".format(session[0])

initSessionDB()
