import requests 
import json
import time
import random
import os

global Cathegories_gist_ID
global Tracker_gist_ID 
global Accounts_gist_ID 


ACCOUNTS = json.loads(os.getenv("ACCOUNTS"))

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GIST_IDS = os.getenv("GIST_IDS").split(",")

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN").strip()

NOTION_API_KEY = os.getenv("NOTION_API_KEY")

NOTION_DATABASE_ID_LIST = os.getenv("NOTION_DATABASE_ID_LIST").split(",")

TrackerFile = "Posting/tracker.json"

accounts_data = ACCOUNTS
system_report_channel_id = 1429473972096995370
system_posting_check_channel_id = 1459189420635848714

Cathegories_gist_ID = GIST_IDS[1]
Tracker_gist_ID = GIST_IDS[0]
Server_ads_gist_ID = GIST_IDS[2]

def get_gist(gist_ID):
    url = f"https://api.github.com/gists/{gist_ID}"
    headers = {
        'Authorization': 'Bearer ' + GITHUB_TOKEN,
        'Content-Type': 'application/json',
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        message = "Gist fetched successfully."
        gist = response.json()
        content = json.loads(next(iter(gist["files"].values()))["content"])
        
        name = next(iter(gist["files"].values()))["filename"]
        return content,message
    else:
        message = f"Failed to fetch gist. Status code: {response.status_code}"
        return None,message
    

def update_gist(gist_id, data, file_name):
    url = f"https://api.github.com/gists/{gist_id}"
    headers = {
        'Authorization': 'Bearer ' + GITHUB_TOKEN,
        'Content-Type': 'application/json',
    }
    data = {
        "files": {
            file_name: {
                "content": json.dumps(data, indent=4)
            }
        }
    }
    response = requests.patch(url, headers=headers, json=data)
    if response.status_code == 200:
        message = "Gist updated successfully."
    else:
        message = f"Failed to update gist. Status code: {response.status_code}"
    return message

def get_data(cathegories_data, tracker_data): # Chooses in which servers it will post with which account
    base_var_post = False
    cathegories = tracker_data["cathegories"]
    cathegory_index = tracker_data["cathegory_index"]

    cathegory_json = cathegories_data[cathegory_index]
    cathegory = cathegories[cathegory_index]
    cathegory_name = cathegories[cathegory_index]["cathegory"]
    account_index = cathegory["account_index"]
    ad_index = cathegory["ad_index"]

    base_var_tracker = tracker_data["base_variables"][cathegory_index][cathegory_name]
    if base_var_tracker == 2:
        base_var_post = True
    else:
        tracker_data["base_variables"][cathegory_index][cathegory_name] = base_var_tracker + 1
    if cathegory_index == 3:
        tracker_data["cathegory_index"] = 0
    else:
        tracker_data["cathegory_index"] = cathegory_index + 1
    if ad_index + 1 == len(cathegory_json["ads"]):
        tracker_data["cathegories"][cathegory_index]["ad_index"] = 0
    else:
        tracker_data["cathegories"][cathegory_index]["ad_index"] = ad_index + 1
    if account_index == 4: 
        cathegory["account_index"] = 1
    else:
        cathegory["account_index"] = account_index + 1
    tracker_data["cathegories"][cathegory_index] = cathegory
    
    return ad_index,cathegory_name, cathegory_json, cathegory_index, account_index,tracker_data, base_var_post # Returns the NAME and the PLACE of the Cathegory and the NUMBER of the account in the account list.

def choose_accounts(accounts_data, cathegory_name, account_index): # Uses the Cathegory name to find the right accounts, chooses one according to the AccountNumber
    for account in accounts_data:
        cathegory = account["cathegory"]
        if cathegory_name in cathegory:
            if account["account_index"] == account_index:
                account_token = account["token"]
                account_username = account["name"]
                return account_token, account_username # Returns the TOKEN and the USERNAME of the account - !maybe change to ID later!
    return None, None
            

def pick_ad(cathegory_json, ad_index): # Uses the AdNumber in tracker.json to pick the ad from the list of ads in the Cathegory's json
    ads = cathegory_json["ads"]
    ad_json = ads[ad_index]
    ad_keywords = ad_json["keywords"]
    base_var_status = ad_json["plan"]

    if base_var_status == "BASE":
        base_var_status = True
    else:
        base_var_status = False

    return ad_json, base_var_status, ad_keywords # Returns the Ad json (1), AdNumber (2), BaseVariable_Status (3) 

def get_forum_tags(account_token, channel_id):
    url = f"https://discord.com/api/v10/channels/{channel_id}"
    headers = {"Authorization": account_token}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        ids = []
        tags = data.get("available_tags", [])
        if not tags:
            return []
        for tag in tags:
            ids.append(tag["id"])
        return ids
    else:
        return None
    
def post_message(cathegory_json, account_token, ad_json, cathegory_name, account_username, base_var_status): # Posts the ads in the channels 
    succesful_posts = 0
    bad_reqeust = False
    unauthorized = False
    errors_log = []
    ad_content = ad_json["content"]
    ad_keywords = ad_json["keywords"]
    urls_json = cathegory_json["urls"] # Gets the IDs of the channels using the JSON
    for url_json in urls_json:
        time.sleep(random.randint(3,5))
        channel_info = url_json["channel"]
        channel_id = channel_info["id"]
        channel_type = channel_info["type"]
        channel_name = channel_info["name"]
        channel_id = channel_info["id"]
        channel_post_base_var = channel_info["post_base_var"]

        guild_info = url_json["guild"]
        guild_name = guild_info["name"]
        guild_id = guild_info["id"]

        if base_var_status == True:
            if channel_post_base_var == False:
                errors_log.append({
                "guild_name": guild_name,
                "guild_id": guild_id,
                "channel_name": channel_name,
                "channel_id": channel_id,
                "status_code": "skipping"
                            })
                continue

        if channel_type == "forum":
            tag_ids = get_forum_tags(account_token, channel_id)
            url = f"https://discord.com/api/v10/channels/{channel_id}/threads"
            headers = {"Authorization": account_token,"Content-Type": "application/json"}
            payload = {
                "name": ad_keywords,
                "message": {"content": ad_content},
                "type": 11, 
                "applied_tags": tag_ids[:4],
                "auto_archive_duration": 1440 
            }
            response = requests.post(url, headers=headers, json=payload)

        if channel_type == "text":
            url = f"https://discord.com/api/channels/{channel_id}/messages"
            headers = {"Authorization": account_token,"Content-Type": "application/json"}
            params = {"content": ad_content,}
            response = requests.post(url, headers=headers, json=params) # Posts the Ad in all of the channels using Token

        status_code = response.status_code
        if status_code != 200:
            errors_log.append({
                "guild_name": guild_name,
                "guild_id": guild_id,
                "channel_name": channel_name,
                "channel_id": channel_id,
                "status_code": status_code
                            })
        else: 
            succesful_posts += 1 
        if status_code == 401:
            unauthorized = True
        elif status_code == 400:
            bad_reqeust = True
    if unauthorized == True:
        errors_log = f"Unauthorized {cathegory_name} | {account_username} <@1148657062599983237>"
    # if BadRequest == True:
    #     ErrorLog = f"Bad Request {Account_Cathegory} | {Account_Number}"
    return errors_log, succesful_posts # Returns a JSON of all the Errors (Status code not 200)
 
def report_system(cathegory_name, account_username, errors_log=None, ad_json=None, skipping=False): # Posts a message to the main report channel
    if skipping == True:
        content = f"**{cathegory_name}** | Cathegory\n**{account_username}** | Account\n\nIt wasnt 6 hours yet - **skipping posting**"
    else:
        if len(errors_log) > 0:
            if isinstance(errors_log, str):
                content = errors_log
            else:
                formatted_errors_log = ""
                number = 1
                for error_json in errors_log:
                    guild_name = error_json["guild_name"]
                    guild_id = error_json["guild_id"]
                    channel_name = error_json["channel_name"]
                    channel_id = error_json["channel_id"]
                    status_code = error_json["status_code"]
                    description = f"{number}.  **{status_code}** | {guild_name} ({guild_id})\n-# Channel: {channel_name} ({channel_id})"
                    formatted_errors_log = f"{formatted_errors_log}\n{description}"
                    number += 1
                content = (f"**{cathegory_name}** | Cathegory\n**{account_username}** | Account\n\n**Errors:**\n{formatted_errors_log}\nAd Content:\n\n`{ad_json['content'][:200]}`")
        else:
            content = ("All Ads posted successfully.")
    url = f"https://discord.com/api/channels/{system_report_channel_id}/messages"
    headers = {
        "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    content = {"content": content}
    response = requests.post(url, headers=headers, json=content)
    if ad_json != None:
        url = f"https://discord.com/api/channels/{system_posting_check_channel_id}/messages"
        content = {"content":ad_json["content"]}
        requests.post(url, headers=headers, json=content)
    if response.status_code == 200:
        message = "System report sent successfully."
    else:
        message = f"Failed to send system posting report. Text: {response.text}"
    return message

def report_customer(ad_json, succesful_posts): # Sends a Report message to the Customer
    ad_contet = ad_json["content"]
    ad_plan = ad_json["plan"]
    ad_posts_left = ad_json["posts_left"]-succesful_posts # Gets all the info from the JSON
    ad_ticket_id = ad_json["ticket_id"]
    ad_keywords = ad_json["keywords"]
    headers = {"Authorization": f"Bot {DISCORD_BOT_TOKEN}","Content-Type": "application/json"}
    data = {
        "embeds": [
            {
                "title": f"{ad_keywords} | {ad_plan}",
                "description": f"{ad_posts_left} posts left",
                "color": int("66107A", 16)
            }
        ]
    }
    url = f"https://discord.com/api/v10/channels/{ad_ticket_id}/messages"
    r = requests.post(url, headers=headers, json=data)
    if r.status_code == 200:
        message = "Customer report sent successfully."
    else:
        message = f"Failed to send customer posting report. Text: {r.text}"
    return message

def update_posts_left(cathegories_data, cathegory_json, cathegory_index, ad_index, ad_keywords, base_vars_data, succesful_posts): # Edits the amount of postings left
    ads = cathegory_json["ads"]
    notion_status_codes = None
    for index,ad in enumerate(ads):
        if ad["keywords"] == ad_keywords:
            old_posts_left = ads[index]["posts_left"]
            new_posts_left = old_posts_left - succesful_posts
        
            cathegories_data[cathegory_index]["ads"][index]["posts_left"] = new_posts_left
            if new_posts_left <= 0:
                cathegory_name = cathegories_data[cathegory_index]["cathegory"]
                cathegories_data[cathegory_index]["ads"][index] = pick_base_var(base_vars_data,cathegory_name)
                notion_status_codes = update_notion([ad_index], "_________", cathegory_name) # Updates Notion
                

    return cathegories_data, notion_status_codes

def track_posting(ad_index, cathegory_place ,cathegories_json):
    new_index = ad_index + 1
    if new_index > 11:
        new_index = 0
    new_keywords = cathegories_json["ads"][new_index]["keywords"]
    old_keywords = cathegories_json["ads"][ad_index]["keywords"]
    cathegory_name = cathegories_json["cathegory"]
    update_notion([ad_index], old_keywords, cathegory_name)
    return update_notion([new_index], f"{new_keywords} 🟢", cathegory_name)
        

def update_notion(ad_indexes_to_update, ad_keyword, cathegory_name):
    if cathegory_name == "RoTech":
        NOTION_DATABASE_ID = NOTION_DATABASE_ID_LIST[0].strip()
    elif cathegory_name == "Aviation":
        NOTION_DATABASE_ID = NOTION_DATABASE_ID_LIST[1].strip()
    elif cathegory_name == "Advertising":
        NOTION_DATABASE_ID = NOTION_DATABASE_ID_LIST[2].strip()
    elif cathegory_name == "Gaming":
        NOTION_DATABASE_ID = NOTION_DATABASE_ID_LIST[3].strip()
    else:
        NOTION_DATABASE_ID = "2d90bcea8f4080d9a67fd07874bbcb61"
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    headers = {'Authorization': 'Bearer ' + NOTION_API_KEY,'Content-Type': 'application/json','Notion-Version': '2022-06-28',}
    data = {
    "sorts": [{
        "property": "Name",
        "direction": "ascending"
    }]
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        data = response.json()
        results = data["results"]
        status_codes = []
        for ad_index in ad_indexes_to_update:
            page = results[ad_index]
            page_id = page["id"]
            new_name = f"{ad_index+1} | {ad_keyword}"

            url = f"https://api.notion.com/v1/pages/{page_id}"
            headers = {
                        'Authorization': 'Bearer ' + NOTION_API_KEY,
                        'Content-Type': 'application/json',
                        'Notion-Version': '2022-06-28',
                    }
            data = {
                "properties": {
                    "Name": {
                        "title": [
                            {"text": {"content": new_name}}
                        ]
                    }
                }
            }
            response = requests.patch(url, headers=headers, json=data)
            if response.status_code == 200:
                status_codes.append("Success")
            else:
                status_codes.append(f"Notion update failed: {response.text}")
        return status_codes
    else:
        print(response.text)

def pick_base_var(base_vars_data,cathegory_name):
    for index,base_var_cathegory_json in enumerate(base_vars_data):
            base_var_cathegory_name = base_var_cathegory_json["cathegory"]
            if cathegory_name == base_var_cathegory_name:
                base_var_json = base_vars_data[index]["ads"][random.randint(0, len(base_var_cathegory_json["ads"])-1)]
                return base_var_json
def main():
    cathegories_data,report_message_gist_GET_cath = get_gist(Cathegories_gist_ID)

    tracker_data, teport_message_gist_GET_tracker = get_gist(Tracker_gist_ID)

    ad_index, cathegory_name, cathegory_json, cathegory_index, account_index, tracker_data_new, base_var_post = get_data(cathegories_data, tracker_data) # Picks the server and account

    account_token, account_username = choose_accounts(accounts_data, cathegory_name, account_index) # Picks the account token and name
    
    ad_json, base_var_status, ad_keywords = pick_ad(cathegory_json, ad_index) # Picks the Ad to post

    base_vars_data,report_message_gist_GET_basevar = get_gist(Server_ads_gist_ID)

    report_message_notion_PATCH_tracker = track_posting(ad_index, cathegory_index, cathegory_json)

    if base_var_status == True: 
        if base_var_post == True:
            tracker_data_new["base_variables"][cathegory_index][cathegory_name] = 0
            ad_json = pick_base_var(base_vars_data,cathegory_name) # Picks a BASE variable Ad

            errors_log, succesful_posts = post_message(cathegory_json, account_token, ad_json, cathegory_name, account_username, True) # Posts the Ad
            report_message_system = report_system(cathegory_name, account_username, errors_log=errors_log, ad_json=ad_json) # Handles andy posting
            report_message_gist_PATCH_tracker = update_gist(Tracker_gist_ID, tracker_data_new, "tracker.json")
            
        else:
            report_message_system = report_system(cathegory_name, account_username,skipping=True)
            report_message_gist_PATCH_tracker = update_gist(Tracker_gist_ID, tracker_data_new, "tracker.json")
        print(f"{report_message_system}\n {report_message_gist_GET_cath, teport_message_gist_GET_tracker, report_message_gist_GET_basevar}\n{report_message_gist_PATCH_tracker}\n{report_message_notion_PATCH_tracker}")

    elif base_var_status == False:
        errors_log, succesful_posts = post_message(cathegory_json, account_token, ad_json, cathegory_name, account_index, False) # Posts the Ad
        report_message_system = report_system(cathegory_name, account_username, errors_log=errors_log, ad_json=ad_json) # Handles any posting
        report_message_system_customer = report_customer(ad_json, succesful_posts) # Sends a report to the customer
        cathegories_data, report_message_notion_PATCH_posts = update_posts_left(cathegories_data, ad_index, cathegory_index, ad_keywords, base_vars_data, succesful_posts) # Edits the amount
        report_message_gist_GET_cath = update_gist(Cathegories_gist_ID,cathegories_data, "cathegories.json")
        teport_message_gist_GET_tracker = update_gist(Tracker_gist_ID, tracker_data_new, "tracker.json")
        print(f"{report_message_system, report_message_system_customer}\n {report_message_gist_GET_cath, teport_message_gist_GET_tracker}\n {report_message_notion_PATCH_posts,report_message_notion_PATCH_tracker}")

    else:
        print("Something is wrong with base variable status", base_var_status)
    
main()

