import os
import datetime
import time

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
import psycopg2

from helpers import apology, buildDirections, getResults, totalDistance, totalTime, directions, getCoords, buildSearch, pointOfInterest, reverseGeo, login_required

# Configure application
app = Flask(__name__)

# test
port = int(os.environ.get("PORT", 5000))
#app.run(debug=True, host='0.0.0.0', port=port)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use Postgres database
db = SQL("postgres://quodhnxqekaccr:42ed38983413e6617acb3c2c55aad545f91166bd886cecf39e646ff9d5f48de0@ec2-107-21-120-104.compute-1.amazonaws.com:5432/d221s270qddtro")

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    """Homepage, show few of history, suggestions of things (gas, food, hotels)"""
    if request.method == "POST":
        return apology(request.form.get("loc"))
        location = reverseGeo(request.form.get("coords"))
        return apology("here2")
        return render_template("index.html", location=location)

    else:
        return render_template("index.html")


@app.route("/history")
@login_required
def history():
    """Show history of Travel Destinations"""
    return apology("TODO")


@app.route("/checkDest", methods=["GET", "POST"])
@login_required
def checkDest():
    """Check information about destination first"""
    if request.method == "POST":
        if (request.form.get("start_street") and request.form.get("start_city") and request.form.get("start_state")):
            start_address = request.form.get("start_street") + "," + request.form.get("start_city") + "," + request.form.get("start_state")
        elif request.form.get("current"):
            start_address = reverseGeo(request.form["current"])
        else:
            return apology("You do not have a starting location")

        if (request.form.get("end_street") and request.form.get("end_city") and request.form.get("end_state")):
            end_address = request.form.get("end_street") + "," + request.form.get("end_city") + "," + request.form.get("end_state")
        else:
            return apology("Please enter a destination.")

        info = {}
        info["directions"] = directions([start_address, end_address])
        time = totalTime([start_address, end_address])
        temp = ""
        if (time // 3600) > 0:
            temp += str(time // 3600) + " hours "
            time %= 3600
        if (time // 60) > 0:
            temp += str(time // 60) + " minutes "
            time %= 60

        temp += str(time) + " seconds"

        info["time"] = temp
        info["distance"] = totalDistance([start_address, end_address])

        return render_template("checkDest.html", info=info)

    else:
        return render_template("checkDest.html")


@app.route("/near", methods=["GET", "POST"])
@login_required
def near():
    """Find Places Nearby"""
    if request.method == "POST":
        if (request.form.get("start_street") and request.form.get("start_city") and request.form.get("start_state")):
            start_address = request.form.get("start_street") + "," + request.form.get("start_city") + "," + request.form.get("start_state")
        elif request.form["current"]:
            start_address = reverseGeo(request.form["current"])
        else:
            return apology("You do not have a starting location")

        if not request.form.get("search"):
            return apology("Please enter what you want to search for.")

        if not request.form.get("number"):
            return apology("Please enter in the number of results you want.")
        elif int(request.form.get("number")) < 1:
            return apology("Please enter in a positve number of searches")

        options = pointOfInterest(start_address, request.form.get("search"), int(request.form.get("number")))

        return render_template("near.html", options=options, search=request.form.get("search").capitalize())
    else:
        return render_template("near.html")


@app.route("/route", methods=["GET", "POST"])
@login_required
def route():
    """Add Navigation Route"""
    if request.method == "POST":
        return apology("TODO")
    else:
        return apology("TODO")

@app.route("/check", methods=["GET"])
def check():
    """Return true if username available, else false, in JSON format"""

    # Gets the potential username of the user
    username = request.args.get("username")

    # If nothing was entered return false
    if username == "":
        return jsonify(False)

    # Checks to see if the username is already registered
    list_users = db.execute("SELECT username FROM users WHERE username = :username", username=username)
    if list_users:
        return jsonify(False)

    return jsonify(True)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":

        # Obtains the username and password entered by the user
        username = request.form.get("username")
        password = request.form.get("password")
        confirm = request.form.get("confirmation")

        # Checks to see if a username was entered and if it is already in the database
        if not username:
            return apology("Please enter a username.")
        elif db.execute("SELECT username FROM users WHERE :username = username", username=username):
            return apology("Username already exists.")

        # Checks to see if a password and confirmation password were entered and if they match
        if not password:
            return apology("Please enter a password.")
        elif not confirm:
            return apology("Please confirm your password.")
        elif password != confirm:
            return apology("Passwords don't match.")

        # Inserts the user into the database
        db.execute("INSERT INTO users(username, hash) VALUES(:username, :hashed)",
                   username=username, hashed=generate_password_hash(password))

        # Saves the session of the user and logs them into the account
        session["user_id"] = db.execute("SELECT id FROM users WHERE :username = username", username=username)[0]["id"]

        return redirect("/")
    else:
        return render_template("register.html")

@app.route("/change", methods=["GET", "POST"])
@login_required
def change():
    """Change the users password"""
    if request.method == "POST":

        # Obtains the old password, new password, and confirmation password
        new_pass = request.form.get("new_pass")
        confirm = request.form.get("confirm")
        old_pass = request.form.get("old_pass")

        # Gets the old password hash value
        old = db.execute("SELECT hash FROM users WHERE id = :user", user=session["user_id"])

        # Checks to see if the old password was entered and if the password in the database and entered password match
        if not old_pass:
            return apology("Please enter your old password.")
        elif not check_password_hash(old[0]["hash"], old_pass):
            return apology("Old password is incorrect.")

        # Checks to see if a new and confirmation password were entered and if they match
        elif not new_pass:
            return apology("Please enter in a new password.")
        elif not confirm:
            return apology("Please confirm your new password.")
        elif new_pass != confirm:
            return apology("The passwords do not match.")

        # Updates the hash value with the new password's hash value
        db.execute("UPDATE users SET hash = :new_pass WHERE id = :user",
                   new_pass=generate_password_hash(new_pass), user=session["user_id"])

        return redirect("/")
    else:
        return render_template("change.html")



def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)


if __name__ == "__main__":
    app.run()
