# freshbooks-tools

A Python client library and tools for the FreshBooks accounting system.  *under development*


## Installation

	$ python3 -m venv venv/3.7
	$ source venv/3.7/bin/activate
    $ pip install coloredlogs maya pyyaml requests requests_oauthlib

## Using it

Authentication is a work in progress. Right now, you have to do this:

    $ python3 freshbooks/client.py

A URL will be displayed on the terminal and opened in the browser,
which will then redirect TO A BOGUS URL on localhost.  That's okay.
Copy URL contains your authentication code. Copy the entire URL (it
looks like
https://localhost:6660/?code=16f117...&state=UP7x09CtSbi...) and paste
it into the terminal window.  An authentication token will be obtained
and saved.

NOTE: The authentication token will expire. Delete
`~/.config/reece/freshbooks/token.json` and reauthenticate.

