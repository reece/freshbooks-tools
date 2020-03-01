import itertools
import json
import logging
import os
import webbrowser

from requests_oauthlib import OAuth2Session
import yaml



_logger = logging.getLogger()



class FreshBooksClient:
    # An FB user may have relationships (e.g., owner) with multiple Businesses
    # A business is associated with an Account
    # A business has Clients

    def __init__(self, session):
        self._session = session
        self._setup()

    def _setup(self):
        p = self.get_profile()
        businesses = [p["business"] for p in p["business_memberships"]]
        assert len(businesses) == 1, "I only support users with one business right now"
        self.business = businesses[0]
        _logger.info(f"Using business {self.business['name']}")
        self.account_id = self.business["account_id"]
        self.business_id = self.business["id"]
        
    def get_clients(self):
        url = f"https://api.freshbooks.com/accounting/account/{self.account_id}/users/clients"
        return self._get(url)["response"]["result"]["clients"]

    def get_profile(self):
        url = "https://api.freshbooks.com/auth/api/v1/users/me"
        return self._get(url)["response"]
    
    def get_projects(self):
        url = f"https://api.freshbooks.com/projects/business/{self.business_id}/projects"
        return self._get(url)["projects"]

    def get_services(self):
        url = f"https://api.freshbooks.com/projects/business/{self.business_id}/services"
        return self._get(url)["services"]

    def get_expenses(self):
        url = f"https://api.freshbooks.com/accounting/account/{self.account_id}/expenses/expenses"
        yield from self._get_paginated(url, "expenses")

    def post_time_entry(self, time_entry):
        url = f"https://api.freshbooks.com/timetracking/business/{self.business_id}/time_entries"
        return self._post(url, json={"time_entry": time_entry})["time_entry"]

    def put_expense(self, id, expense_data):
        url = f"https://api.freshbooks.com/accounting/account/{self.account_id}/expenses/expenses/{id}"
        return self._put(url, json=expense_data)["response"]["result"]["expense"]

    def make_client_id_map(self):
        return {c["organization"]: c["id"] for c in fbc.get_clients()}

    def make_client_project_id_map(self):
        projects = fbc.get_projects()
        projects.sort(key=lambda p: str(p["client_id"]))
        p_gi = itertools.groupby(projects, key=lambda p: p["client_id"])
        return {client_id: {p["title"]: p["id"] for p in pi} for client_id, pi in p_gi}

    def make_service_id_map(self):
        return {s["name"]: s["id"] for s in fbc.get_services()}

    
    def expenses_include_receipt(self, expenses=None):
        if not expenses:
            expenses = [e
                        for e in self.get_expenses()
                        if not e["include_receipt"]]
        for e in expenses:
            self.put_expense(e["id"], {"expense": {"include_receipt": True}})
            _logger.info(f"{e['date']} {e['amount']['amount']} @ {e['notes']}: marked include_receipt")

    def find_outstanding_expenses_without_receipt(self, expenses=None):
            expenses = [e
                        for e in self.get_expenses()
                        if (e["status"] == 1  # outsanding
                            and not e["has_receipt"])]
            return expenses


    ############################################################################
    # INTERNAL

    def _get(self, url):
        r = self._session.get(url)
        r.raise_for_status()
        return r.json()

    def _get_paginated(self, url, key):
        """like _get, but assume that return includes structure like
        "response": {
          "result": {
            "page": 1,
            "pages": 1,
            ...
        }}
        and *yield* items from it
        """

        pages = None
        p = 1
        while True:
            urlp = url + f"?page={p}"
            _logger.info(f"Fetching page {p}/{pages} of {url}")
            r = self._get(urlp)
            yield from r["response"]["result"][key]
            pages = int(r["response"]["result"]["pages"])
            if p >= pages:
                break
            p += 1

    def _post(self, url, json):
        r = self._session.post(url, json=json)
        r.raise_for_status()
        return r.json()
        
    def _put(self, url, json):
        r = self._session.put(url, json=json)
        r.raise_for_status()
        return r.json()
        


def get_session():
    config_dir = os.path.expanduser("~/.config/reece/freshbooks")
    config_fn = os.path.join(config_dir, "creds.yaml")
    creds = yaml.safe_load(open(config_fn))
    client_id = creds["client_id"]
    client_secret = creds["client_secret"]

    authorization_base_url = "https://my.freshbooks.com/service/auth/oauth/authorize"
    token_url = "https://api.freshbooks.com/auth/oauth/token"
    redirect_uri = "https://localhost:6660/"
     
    token_fn = os.path.join(config_dir, "token.json")
    if os.path.exists(token_fn):
        token = json.load(open(token_fn))
        sess = OAuth2Session(client_id, token=token)
    else:
        sess = OAuth2Session(client_id, redirect_uri = redirect_uri)
         
        # Redirect user to FreshBooks for authorization
        authorization_url, state = sess.authorization_url(authorization_base_url)
        print('Please go here and authorize,', authorization_url)
        webbrowser.open(authorization_url)
         
        # Get the authorization verifier code from the callback url
        redirect_response = input('Paste the full redirect URL here:')
         
        # Fetch the access token
        sess.fetch_token(token_url, client_secret = client_secret,
                         authorization_response = redirect_response)
        json.dump(sess.token, open(token_fn, "w"))

    return sess



if __name__ == "__main__":
    import coloredlogs

    coloredlogs.install(level="INFO")

    sess = get_session()
    fbc = FreshBooksClient(sess)
    self = fbc

    # for te in generate_clingen_time_entries(fbc, sys.argv[1]):
    #     r = fbc.post_time_entry(te)
    #     _logger.info(f"loaded {r['duration']} @ {r['started_at']}")

    client_id_map = fbc.make_client_id_map()
    client_project_id_map = fbc.make_client_project_id_map()
    service_id_map = fbc.make_service_id_map()
