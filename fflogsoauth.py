import requests
import time

# FFLogs OAuth Token URL
URL_OAUTH_TOKEN = "https://www.fflogs.com/oauth/token"
# FFLogs Client API
URL_API = "https://www.fflogs.com/api/v2/client"

# FFLogs OAuth Client
class FFLogsOAuth:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.expire = 0
        self.token = ''

    # Get OAuth Token / Refresh Token
    def _get_token(self):
        rtime = time.time()
        print(self.expire, rtime)
        if self.expire < rtime:
            data = {
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
            }
            r = requests.post(URL_OAUTH_TOKEN, data=data)
            r_json = r.json()
            self.expire = rtime + r_json['expires_in']
            self.token = r_json['access_token']
            
        return self.token

    # Performs GraphQL Query on FFLogs API
    def query(self, query):
        token = self._get_token()

        headers = {'Authorization': 'Bearer ' + token}
        r = requests.get(URL_API, headers=headers, json={'query': query})
        return r.json()