"""
Name: Gyazo-to-imgur bot

Purpose: To convert Gyazo links to imgur links, as imgur is objectively better for RES users.

Author: arrivance
"""

import praw
import json
import utility
import re

from imgurpython import ImgurClient

"""
Configuration
"""
if utility.file_checker("login.json") == False:
    print("You are required to make a login.json file for the program to work.")

# opens the login.json file with all of the authentication dtails
with open("login.json") as data_file:
    # dumps all the login details into the program 
    login_details = json.load(data_file)

gyazo_regex = re.compile("https?:\/\/gyazo\.com\/[a-z0-9]+")

# initialises PRAW instance
# and creates a user agent
user_agent = login_details["reddit_ua"]
print("Gyazo to imgur converter by /u/arrivance")
print("User agent:", user_agent)

r = praw.Reddit(user_agent)
r.set_oauth_app_info(client_id=login_details["reddit_client_id"], client_secret=login_details["reddit_client_secret"], redirect_uri=login_details["reddit_redirect_uri"])

"""
reddit auth
"""
access_token = utility.reddit_oauth_token(login_details, user_agent)

# gets the access information
r.set_access_credentials({"identity", "submit"}, access_token)
# authenticates the user with reddit
authenticated_user = r.get_me()

"""
imgur auth
"""
# logins into the imgurclient using the login details provided
imgur_client = ImgurClient(login_details["imgur_client_id"], login_details["imgur_secret"])

if utility.file_checker("commented.json") == False:
    structure = {
        "comment_ids":"[]", 
        "disallowed":"[]",
        "submission_ids":"[]"
    }
    print("It is recommended to follow Bottiquete, and to add a list of blacklisted subreddits to disallowed.")
    utility.file_maker("commented.json", structure)

# always loops
while True: 
    # opens the json file
    with open("commented.json") as data_file: 
        # dumps the json file
        raw_json = json.load(data_file)
        # puts the handled_comments and submissions in memory
        handled_comments = raw_json["comment_ids"]
        disallowed_subreddits = raw_json["disallowed"]

    # checks all the comments being posted on reddit at all
    all_comments = praw.helpers.comment_stream(r, "all", verbosity=3)

    # goes through all the comments
    for comment in all_comments:
        matches = gyazo_regex.findall(comment.body.lower())
        if len(matches) != 0 and comment.id not in handled_comments: 
            for link in matches:
                gyazo_link = utility.gyazo_link_parser(link)
                imgur_upload = utility.imgur_uploader(gyazo_link, imgur_client)
                if imgur_upload != False:
                    utility.comment_poster(comment, utility.comment_prep(imgur_upload))
        # and then appends the comment to the handled comments so we don't recheck
            if comment.id not in handled_comments:
                raw_json["comment_ids"].append(comment.id)
                with open("commented.json", "w") as data_file:
                    json.dump(raw_json, data_file)
