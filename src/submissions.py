"""
Name: Gyazo-to-imgur bot

Purpose: To convert Gyazo links to imgur links, as imgur is objectively better for RES users.
Also contains a mini-webserver to make authentication easier.

Author: arrivance
"""

import praw
import webbrowser
import sys
import urllib.request
import json
import utility

from imgurpython import ImgurClient
from tkinter import Tk
from bs4 import BeautifulSoup
from flask import Flask, request

"""
Configuraation
"""
# initialises PRAW instance
# and creates a user agent
r = praw.Reddit("Gyazo-to-imgur by /u/arrivance (version b0.7)")

# opens the login.json file with all of the authentication dtails
with open("login.json") as data_file:
    # dumps all the login details into the program 
    login_details = json.load(data_file)

"""
The OAuth setup 
Creates a Flask webserver, and then gives easy instructions to OAuth. 
Required as reddit is moving away from cookie based logins
"""
# creates an oauth app with the provided login details
r.set_oauth_app_info(client_id=login_details["reddit_client_id"], client_secret=login_details["reddit_client_secret"], redirect_uri=login_details["reddit_redirect_uri"])

# creates an instance of flask
app = Flask(__name__)
@app.route("/")
def homepage(): 
    """
    Initial OAuth link
    """
    return "<a href=%s>Auth with the reddit API</a>" % r.get_authorize_url("uniqueKey", ["identity", "submit"], True)

@app.route("/authorize_callback")
def authorized():
    """
    After we"ve successfully logged into the reddit API, we then parse what it returns to us
    """
    global code
    state = request.args.get("state", "")
    code = request.args.get("code", "")

    # instructs the user to click a link to shutdown the flask instance
    return "Authentication with the reddit API was successful. Please click to close authentication: <a href='http://127.0.0.1:65010/shutdown'>shutdown</a>."

@app.route("/shutdown")
def shutdown():
    """
    Shutdowns the Flask instance to proceed
    """
    func = request.environ.get("werkzeug.server.shutdown")
    if func is None: 
        print("Err")

    func()

# if you don't want to auth via the web server, you can auth via the web client
if "-manauth" in sys.argv:
    global code

    auth_url = r.get_authorize_url("uniqueKey", ["identity", "submit"], True)

    # adds the url to the clipboard
    clip = Tk()
    clip.withdraw()
    clip.clipboard_clear()
    clip.clipboard_append(auth_url)
    clip.destroy()

    print("Authentication URL has been successfully copied to the clipboard. Please copy and paste this into a web browser.")
    print("URL if clipboard copying has not been succesful: ", auth_url)

    # makes the user paste it in
    print("\n\nAfter clicking 'Accept' on the page, please copy and paste from where it says 'code=' in the address bar. Paste it when the program asks.")
    code = input("Paste the code as asked before: ")
else:
    # creates the web server
    webbrowser.open("http://127.0.0.1:65010")
    app.run(debug=False, port=65010)

# logins into the imgurclient using the login details provided
imgur_client = ImgurClient(login_details["imgur_client_id"], login_details["imgur_secret"])

# gets the access information
access_information =  r.get_access_information(code)
# authenticates the user with reddit
authenticated_user = r.get_me()

if utility.file_checker("commented.json") == False:
    structure = {
        "comment_ids":"", 
        "disallowed":"",
        "submission_ids":""
    }
    utility.file_maker("commented.json", structure)


# always loops
while True: 
    # opens the json file
    with open("commented.json") as data_file: 
        # dumps the json file
        raw_json = json.load(data_file)
        # puts the handled_comments and submissions in memory
        handled_submissions = raw_json["submission_ids"]
        disallowed_subreddits = raw_json["disallowed"]

    # checks all the submissions in reddit
    subreddit = praw.helpers.submission_stream(r, "all", verbosity=1)

    # checks all the submission in new
    for submission in subreddit:
        # gets the domain, url and id
        submission_url = submission.url
        submission_domain = submission.domain
        submission_id = submission.id

        if submission_domain == "gyazo.com" and submission_id not in handled_submissions:
            if submission_url > 17: 
                gyazo_link = utility.gyazo_link_parser(submission_url)
                imgur_upload = utility.imgur_uploader(gyazo_link)
                if imgur_upload != False:
                    utility.comment_poster(submission, utility.comment_prep(imgur_upload))

        if submission_id not in handled_submissions:
            raw_json["submission_ids"].append(submission_id)
            with open("commented.json", "w") as data_file:
                json.dump(raw_json, data_file)