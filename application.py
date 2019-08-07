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

from helpers import apology, login_required, buildDirections, getResults, totalDistance, totalTime, directions, getCoords, buildSearch, pointOfInterest, reverseGeo

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


@app.route("/")
@login_required
def index():
    """Homepage, show few of history, suggestions of things (gas, food, hotels)"""
    #routes = db.execute("SELECT * FROM routes WHERE id = :user", user = user)
    new = True

    #if routes:
    #    return apology("TODO")

    if new:
        return render_template("index.html")
    else:
        return render_template("index.html")


@app.route("/history")
def history():
    """Show history of Travel Destinations"""
    return apology("TODO")


@app.route("/checkDest", methods=["GET", "POST"])
def checkDest():
    """Check information about destination first"""
    if request.method == "POST":
        if (request.form.get("start_street") and request.form.get("start_city") and request.form.get("start_state")):
            start_address = request.form.get("start_street") + "," + request.form.get("start_city") + "," + request.form.get("start_state")
        elif request.form.get("current"):
            start_address = reverseGeo(request.form["lat"], request.form["lng"])
        else:
            return apology("You do not have a starting location")

        if (request.form.get("start_street") and request.form.get("start_city") and request.form.get("start_state")):
            end_address = request.form.get("end_street") + "," + request.form.get("end_city") + "," + request.form.get("end_state")
        else:
            return apology("Please enter a destination.")

        info = {}
        info["directions"] = directions([start_address, end_address])
        info["time"] = totalTime([start_address, end_address])
        info["distance"] = totalDistance([start_address, end_address])

        return render_template("checkDest.html", info=info)

    else:
        return render_template("checkDest.html")


@app.route("/near", methods=["GET", "POST"])
def near():
    """Find Places Nearby"""
    if request.method == "POST":
        return apology("TODO")
    else:
        return apology("TODO")



@app.route("/change", methods=["GET", "POST"])
def change():
    """Change the users password (Check if implementation is similar or not"""
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


@app.route("/route", methods=["GET", "POST"])
@login_required
def route():
    """Add Navigation Route"""
    if request.method == "POST":
        return apology("TODO")
    else:
        return apology("TODO")


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
