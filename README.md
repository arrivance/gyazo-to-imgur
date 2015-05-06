# gyazo-to-imgur
A PRAW-based reddit bot that'll convert Gyazo links to imgur links. 

Modules 
=========

comments.py checks all reddit comments being posted from the moment of it being launched. If it finds a link with Gyazo mentioned, it'll convert it into a Imgur link.

submissions.py checks all reddit submissions to check if they're on the Gyazo domain. If they are, it'll mirror the link to imgur (slightly untested).

comments.py is at a stable stage, and should be safe to use. submissions.py is still slightly risque.