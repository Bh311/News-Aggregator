import requests
from requests_oauthlib import OAuth1

# Twitter API credentials from your config
API_KEY = ""
API_SECRET = ""
ACCESS_TOKEN = ""
ACCESS_TOKEN_SECRET = ""

auth = OAuth1(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

# Step 1: Get your user ID
user_url = "https://api.twitter.com/2/users/me"
headers = {"User-Agent": "v2UserLookupPython"}
response = requests.get(user_url, auth=auth)
user_data = response.json()
user_id = user_data.get("data", {}).get("id")

# Step 2: Get your lists
lists_url = f"https://api.twitter.com/2/users/{user_id}/owned_lists"
response = requests.get(lists_url, auth=auth)
lists_data = response.json()

# Print all list names and their IDs
for lst in lists_data.get("data", []):
    print(f"List Name: {lst['name']} | List ID: {lst['id']}")
