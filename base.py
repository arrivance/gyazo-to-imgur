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
r = praw.Reddit("Gyazo-to-imgur bot by /u/arrivance (currently testing)")

with open("login.json") as data_file: 
    login_details = json.load(data_file)

"""
The OAuth setup 
Creates a Flask webserver, and then gives easy instructions to OAuth. 
Required as reddit is moving away from cookie based logins
"""
r.set_oauth_app_info(client_id=login_details["reddit_client_id"], client_secret=login_details["reddit_client_secret"], redirect_uri=login_details["reddit_redirect_uri"])

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

if "-manauth" in sys.argv:
    global code

    auth_url = r.get_authorize_url("uniqueKey", ["identity", "submit"], True)
    clip = Tk()
    clip.withdraw()
    clip.clipboard_clear()
    clip.clipboard_append(auth_url)
    clip.destroy()

    print("Authentication URL has been successfully copied to the clipboard. Please copy and paste this into a web browser.")
    print("URL if clipboard copying has not been succesful: ", auth_url)

    print("\n\nAfter clicking 'Accept' on the page, please copy and paste from where it says 'code=' in the address bar. Paste it when the program asks.")
    code = input("Paste the code as asked before: ")
else:
    webbrowser.open("http://127.0.0.1:65010")
    app.run(debug=False, port=65010)

"""
Functions
"""

def gyazo_link_parser(link):
    """
    Parses Gyazo links into their raw (.png or .gif) form (i.gyazo)
    """ 
    response = urllib.request.urlopen(link)
    html = response.read()

    parsed = BeautifulSoup(html)
    title = parsed.title.string
    print(str(title))

    return "http://i.gyazo.com/" + title.replace("Gyazo - ", "")

def imgur_uploader(link): 
    """
    Uploads passed image to imgur, and then outputs the link from the JSON/dict provided.
    I"m calling it JSON. 
    """
    try: 
        uploaded_image = imgur_client.upload_from_url(url=link, config=None, anon=True)
    except: 
        print("Error when uploading the image to imgur.")
        return False
    else:
        print("Successful convert of", link, "to an imgur link", uploaded_image["link"])
        return uploaded_image["link"]

def file_reader(filename):
    """
    Simple file reader so we can store (and avoid) already parsed comments
    """
    open_file = open(filename, "r+")
    open_file_contents = open_file.readlines()
    open_file.close()

    open_file_san = []

    for x in open_file_contents:
        open_file_san.append(x.replace("\n", ""))

    return open_file_san

def file_writer(filename, towrite):
    """
    Simple file writer so we can store (and avoid) already parsed comments
    """
    open_file = open(filename, "r+")
    open_file_contents = open_file.read()

    open_file.write(open_file_contents + "\n" + towrite + "\n")

    open_file.close()
    
def comment_prep(content): 
    """
    Prepares the comment so we can have sme basic context.
    """
    text = "Imgur link: " + content
    text += "\n\n\n------\n"
    text += "This action was performed by a bot. Message +/u/arrivance for further details."
    return text

imgur_client = ImgurClient(login_details["imgur_client_id"], login_details["imgur_secret"])

access_information =  r.get_access_information(code)
authenticated_user = r.get_me()

while True: 
    with open("commented.json") as data_file: 
        raw_json = json.load(data_file)
        handled_comments = raw_json["comment_ids"]


    subreddit = r.get_subreddit("arrivance")
    for submission in subreddit.get_hot(limit=10):
        flat_comments = praw.helpers.flatten_tree(submission.comments)
        for comment in flat_comments: 
            if "http://gyazo.com" in comment.body and comment.id not in handled_comments:
                stuff = comment.body.split()
                for x in stuff: 
                    if "http://gyazo.com" in x and len(x) > 17:
                            print(x)
                            gyazo_link = gyazo_link_parser(x) 
                            imgur_upload = imgur_uploader(gyazo_link)
                            try: 
                                comment.reply(comment_prep(imgur_upload))
                            except praw.errors.RateLimitExceeded as e:
                                print("Rate limit exceeded:", e)
                            except praw.errors.APIException as e:
                                print("API Exception:", e)
                            except:
                                print("Other unknown fault.")
                            else: 
                                print("Successfully commented on comment ID", comment.id)
                    elif "gyazo.net" in x:
                        x = "http://" + x
                        if len(x) > 17:
                            imgur_upload = imgur_uploader(gyazo_link_parser(x))
                            try: 
                                comment.reply(comment_prep(imgur_upload))
                            except praw.errors.RateLimitExceeded as e:
                                print("Rate limit exceeded:", e)
                            except praw.errors.APIException as e:
                                print("API Exception:", e)
                            except:
                                print("Other unknown fault.")
                            else: 
                                print("Successfully commented on comment ID", comment.id)
            if comment.id not in handled_comments:
                raw_json["comment_ids"].append(comment.id)
                with open("commented.json", "w") as data_file:
                    json.dump(raw_json, data_file)
