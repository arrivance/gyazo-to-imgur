import praw
import webbrowser
import sys
import urllib.request
import json
import os.path

from imgurpython import ImgurClient
from tkinter import Tk
from bs4 import BeautifulSoup
from flask import Flask, request

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

def file_checker(filename): 
	if os.path.isfile(filename) == True:
		return True
	else:
		return False

def file_maker(filename, structure):
	with open(filename, "w") as data_file:
		json.dump(structure, filename)
	return True