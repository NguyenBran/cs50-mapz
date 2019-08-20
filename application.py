import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, buildDirections, getResults, totalDistance, totalTime, directions, getCoords, buildSearch, pointOfInterest, reverseGeo, login_required

# Configure application
app = Flask(__name__)

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


@app.route("/", methods=["GET"])
@login_required
def index():
    """Homepage, suggestions of things (gas, food, hotels), with a form to route the user"""
    return render_template("index.html")


@app.route("/display", methods=["GET"])
@login_required
def display():
    # Gets the location of the user and then looks for food, dessert, gas, and hotels in the area
    location = reverseGeo(request.args.get("location"))
    food = pointOfInterest(location, "restaurant", 4)
    dessert = pointOfInterest(location, "dessert", 4)
    gas = pointOfInterest(location, "gas", 4)
    hotel = pointOfInterest(location, "hotel", 4)

    # Stores the information in a dictionary that will be sent back
    info = {
        "food": food,
        "dessert": dessert,
        "gas": gas,
        "hotel": hotel
    }

    return jsonify(info)


@app.route("/update", methods=["GET"])
@login_required
def update():
    # Gets the current location of the user and their destination
    start = reverseGeo(request.args.get("location"))
    end = request.args.get("destination")

    # Gathers information about the route and returns it back into the html file to be displayed
    info = buildInfo(start, end)

    return jsonify(info)


@app.route("/history")
@login_required
def history():
    """Show history of Travel Destinations"""

    # Gathers information about the users searches and routes from the database
    name = db.execute("SELECT username FROM users WHERE id = :user", user=session["user_id"])[0]["username"]
    searches = db.execute("SELECT * FROM search WHERE id = :user", user=session["user_id"])
    routes = db.execute("SELECT * FROM routes WHERE id = :user", user=session["user_id"])

    # Turns the result of the searches into a list
    for search in searches:
        search["results"] = search["results"].split("<>")

    return render_template("history.html", searches=searches, routes=routes, name=name)


@app.route("/route", methods=["GET", "POST"])
@login_required
def route():
    """Check information about destination first"""
    if request.method == "POST":

        # Checks to see if all of the fields for the starting address were filled
        if (request.form.get("start_street") and request.form.get("start_city") and request.form.get("start_state")):
            start_address = (request.form.get("start_street") + "," + request.form.get("start_city") +
                             "," + request.form.get("start_state"))

        # Checks to see if the user wanted to use their current location instead
        elif request.form.get("current"):
            start_address = reverseGeo(request.form["current"])
        else:
            return apology("You do not have a starting location")

        # Checks to see if all of the fields for the end address were filled in
        if (request.form.get("end_street") and request.form.get("end_city") and request.form.get("end_state")):
            end_address = request.form.get("end_street") + "," + request.form.get("end_city") + "," + request.form.get("end_state")
        else:
            return apology("Please enter a destination.")

        # Gathers information about the route
        info = buildInfo(start_address, end_address)

        # Inserts the information into the database to use for the history of the user
        db.execute("INSERT INTO routes VALUES(:user, :start, :end, :distance, :time)",
                   user=session["user_id"], start=start_address, end=end_address, distance=info["distance"], time=totalTime([start_address, end_address]))

        return render_template("route.html", info=info)

    else:
        return render_template("route.html")


@app.route("/near", methods=["GET", "POST"])
@login_required
def near():
    """Find Places Nearby"""
    if request.method == "POST":

        # Checks to see if all of the fields for the starting address were filled
        if (request.form.get("start_street") and request.form.get("start_city") and request.form.get("start_state")):
            start_address = (request.form.get("start_street") + "," + request.form.get("start_city") +
                             "," + request.form.get("start_state"))

        # Checks to see if the user wanted to use their current location
        elif request.form["current"]:
            start_address = reverseGeo(request.form.get("current"))
        else:
            return apology("You do not have a starting location")

        # Checks to see if the user wanted to insert their own search
        if request.form.get("search") == "other":
            search = request.form.get("other")

        # If not, then it will save the search the user selected
        else:
            search = request.form.get("search")

        # Checks to see if a number was put in, also if it was positive
        if not request.form.get("number"):
            return apology("Please enter in the number of results you want.")
        elif int(request.form.get("number")) < 1:
            return apology("Please enter in a positve number of searches")

        # Gathers the information on the results of the search in the area
        options = pointOfInterest(start_address, search, int(request.form.get("number")))

        # Inserts the information and data into the table
        db.execute("INSERT INTO search VALUES(:user, :start, :search, :results)",
                   user=session["user_id"], start=start_address, search=search, results=options)

        return render_template("near.html", options=options, search=search.capitalize())
    else:
        return render_template("near.html")


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

    # Forget any username
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

        # Increments the sequence to avoid the lastval error with sequencing
        db.execute("SELECT nextval('users_id_seq')")

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""
    # Forget any username
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

        # Logs in the user with their id as a saved value for the duration of the session
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


# Builds the information used for routing the user
def buildInfo(start, end):
    info = {}

    # Gathers the steps and directions on how to get to the destination
    info["directions"] = directions([start, end])

    # Gathers the total time it would take and formats it into hours, minutes, and seconds
    time = totalTime([start, end])
    temp = time
    text = ""
    if (temp // 3600) > 0:
        text += str(temp // 3600) + " hours "
        temp %= 3600
    if (temp // 60) > 0:
        text += str(temp // 60) + " minutes "
        temp %= 60

    text += str(temp) + " seconds"

    # Fills in the information for the route directions that will be displayed then returns this
    info["time"] = text
    info["distance"] = totalDistance([start, end])
    info["destination"] = end

    return info


if __name__ == "__main__":
    app.run()
