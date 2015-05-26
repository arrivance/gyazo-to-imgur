import praw
import urllib.request
import json
import requests
import requests.auth
import os.path
import re

from imgurpython import ImgurClient
from bs4 import BeautifulSoup

imgur_gif_regex = re.compile("https?:\/\/i\.imgur\.com\/[a-z0-9]+.gif")

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

def imgur_uploader(link, imgur_client): 
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
        if len(imgur_gif_regex.findall(uploaded_image["link"])) != 0: 
            return uploaded_image["link"] + "v"
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

def reddit_oauth_token(login_details, user_agent):
    client_auth = requests.auth.HTTPBasicAuth(login_details["reddit_client_id"], login_details["reddit_client_secret"])
    post_data = {"grant_type": "password", "username": login_details["reddit_user"], "password": login_details["reddit_pass"]}
    headers = {"User-Agent": user_agent}
    print("Attempting to get the access_token from reddit...")
    response = requests.post("https://www.reddit.com/api/v1/access_token", auth=client_auth, data=post_data, headers=headers)
    access_token = response.json()["access_token"]
    print("access_token succesfully gotten:", access_token)
    return access_token
