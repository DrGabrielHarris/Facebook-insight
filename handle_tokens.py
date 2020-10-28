import json
import logging

import facebook
import requests

logging.basicConfig(
    level=logging.INFO, format="[%(asctime)s] %(message)s", datefmt="%d/%m/%y %H:%M:%S"
)

# get user, app, and page info
with open("facebook.json", "r") as f:
    data = json.load(f)

user_short_token = data["user"]["short_token"]
user_long_token = data["user"]["long_token"]

app_id = data["app"]["id"]
app_secret = data["app"]["secret"]

page_token = data["page"]["token"]
sdk_version = data["sdk_version"]


def exchange_token(token: str) -> str:
    """Post request to exchange given token

    Args:
        token (str): token to echange. Either long lived or permanant

    Returns:
        str: new permanant token
    """

    url = "https://graph.facebook.com/oauth/access_token"

    payload = {
        "grant_type": "fb_exchange_token",
        "client_id": app_id,
        "client_secret": app_secret,
        "fb_exchange_token": token,
    }

    try:
        response = requests.get(
            url,
            params=payload,
            timeout=5,
        )
    except requests.exceptions.Timeout as e:
        logging.error("TimeoutError", e)
    else:
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logging.error("HTTPError", e)
        else:
            response_json = response.json()
            logging.info(response_json)
            return response_json["access_token"]


# if no long lived token exists yet, get one, then use it to get a permanent token
if user_long_token == "None":

    user_long_token = exchange_token(user_short_token)
    data["user"]["long_token"] = user_long_token

    graph = facebook.GraphAPI(access_token=user_long_token, version=sdk_version)
    pages_data = graph.get_object("/me/accounts")

    page_token = pages_data["data"][0]["access_token"]
    data["page"]["token"] = page_token

    # update page id in json (for reference only)
    page_id = pages_data["data"][0]["id"]
    data["page"]["id"] = page_id

# if a long lived token does exist, exchange the permanent token
else:
    page_token = exchange_token(page_token)
    data["page"]["token"] = page_token

    # open json file and update data
    with open("facebook.json", "w") as f:
        json.dump(data, f, indent=4)
