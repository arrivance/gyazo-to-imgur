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

"""
Functions
"""

def gyazo_link_parser(link):
    """
    Parses Gyazo links into their raw (.png or .gif) form (i.gyazo)
    """ 
    # opens the gyazo link
    response = urllib.request.urlopen(link)
    # reads the reponse
    html = response.read()

    # parses the html using beautifulsoup, and gives me the image link
    parsed = BeautifulSoup(html)
    return parsed.img['src']

    # old method of handling gyazo links
    #title = parsed.title.string
    #print(str(title))

    #return "http://i.gyazo.com/" + title.replace("Gyazo - ", "")

def imgur_uploader(link): 
    """
    Uploads passed image to imgur, and then outputs the link from the JSON/dict provided.
    I"m calling it JSON. 
    """
    # tries to upload the image to imgur
    try: 
        uploaded_image = imgur_client.upload_from_url(url=link, config=None, anon=True)
    except: 
        # if it crashes, it'll just return False
        print("Error when uploading the image to imgur.")
        return False
    else:
        # otherwise, yay, we return a link
        print("Successful convert of", link, "to an imgur link", uploaded_image["link"])
        return uploaded_image["link"]
    
def comment_prep(content): 
    """
    Prepares the comment so we can have sme basic context.
    """

    # same comment structure, so we'll just do it in a function
    text = "Imgur link: " + content
    text += "\n\n\n------\n"
    text += "This action was performed by a bot. Message +/u/arrivance for further details."
    return text

def comment_poster(comment, content): 
    try:
        comment.reply(content)
    except praw.errors.RateLimitExceeded as e:
        print("Rate limit exceeded:", e)
    except praw.errors.APIException as e:
        print("API Exception:", e)
    except:
        print("Other unknown fault.")
    else: 
        print("Successfully commented on comment ID", comment.id)

# logins into the imgurclient using the login details provided
imgur_client = ImgurClient(login_details["imgur_client_id"], login_details["imgur_secret"])

# gets the access information
access_information =  r.get_access_information(code)
# authenticates the user with reddit
authenticated_user = r.get_me()

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
                gyazo_link = gyazo_link_parser(submission_url)
                imgur_upload = imgur_uploader(gyazo_link)
                if imgur_upload != False:
                    comment_poster(submission, comment_prep(imgur_upload))

        if submission_id not in handled_submissions:
            raw_json["submission_ids"].append(submission_id)
            with open("commented.json", "w") as data_file:
                json.dump(raw_json, data_file)