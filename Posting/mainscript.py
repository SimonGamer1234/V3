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

Accounts_data = ACCOUNTS
PostingChanenelID = 1429473972096995370

Cathegories_gist_ID = GIST_IDS[1]
Tracker_gist_ID = GIST_IDS[0]
Server_ads_gist_ID = GIST_IDS[2]

def Get_Gist(gist_ID):
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
        print(name, content, message)
        return content,name, message
    else:
        message = f"Failed to fetch gist. Status code: {response.status_code}"
        return None,None, message
    

def Update_Gist(gist_id, data, file_name):
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

def Get_Data(Cathegories_data, Tracker_data): # Chooses in which servers it will post with which account
    Base_Variable_Check = False
    Accounts = Tracker_data["Accounts"]
    if Tracker_data["Test"] == True:
        Cathegory_NAME = "Test"
        Cathegory_Place = 4
        Cathegory_JSON = Cathegories_data[Cathegory_Place]
        Plan = Accounts[Cathegory_Place]
        AccountNumber = Plan["AccountNumber"]
        AdNumber = Plan["AdNumber"]
        if AdNumber == 2:
            Tracker_data["Accounts"][Cathegory_Place]["AdNumber"] = 0
        else:
            Tracker_data["Accounts"][Cathegory_Place]["AdNumber"] = AdNumber + 1
        if AccountNumber == 2:
            Tracker_data["Accounts"][4]["AccountNumber"] = 1
        else:
            Tracker_data["Accounts"][4]["AccountNumber"] = AccountNumber + 1
    else:
        Cathegory_Place = Tracker_data["Number"]
        print(f"Cathegory Number: {Cathegory_Place}")

        Cathegory_JSON = Cathegories_data[Cathegory_Place]
        Plan = Accounts[Cathegory_Place]
        Cathegory_NAME = Cathegories_data[Cathegory_Place]["Cathegory"]
        AccountNumber = Plan["AccountNumber"]
        AdNumber = Plan["AdNumber"]
        Base_Variable_Tracker = Tracker_data["Base-Variables"][Cathegory_Place][Cathegory_NAME]
        if Base_Variable_Tracker == 2:
            Base_Variable_Check = True
        else:
            Tracker_data["Base-Variables"][Cathegory_Place][Cathegory_NAME] = Base_Variable_Tracker + 1
        if Cathegory_Place == 3:
            Tracker_data["Number"] = 0
        else:
            Tracker_data["Number"] = Cathegory_Place + 1
        if AdNumber + 1 == len(Cathegory_JSON["Ads"]):
            Tracker_data["Accounts"][Cathegory_Place]["AdNumber"] = 0
        else:
            Tracker_data["Accounts"][Cathegory_Place]["AdNumber"] = AdNumber + 1
        if AccountNumber == 4: 
            Plan["AccountNumber"] = 1
        else:
            Plan["AccountNumber"] = AccountNumber + 1
        Tracker_data["Accounts"][Cathegory_Place] = Plan
    
    return AdNumber,Cathegory_NAME, Cathegory_JSON, Cathegory_Place, AccountNumber,Tracker_data, Base_Variable_Check # Returns the NAME and the PLACE of the Cathegory and the NUMBER of the account in the account list.

def Choose_Accounts(Accounts_data, Cathegory_NAME, AccountNumber): # Uses the Cathegory name to find the right accounts, chooses one according to the AccountNumber
    for account in Accounts_data:
        cathegory = account["Cathegory"]
        if Cathegory_NAME in cathegory:
            if account["AccountNumber"] == AccountNumber:
                AccountToken = account["Token"]
                AccountName = account["Name"]
                return AccountToken, AccountName # Returns the TOKEN and the USERNAME of the account - !maybe change to ID later!
    
    print("Error: Account not found")
    return None, None
            

def Pick_Ad(Cathegory_JSON, AdNumber): # Uses the AdNumber in tracker.json to pick the ad from the list of ads in the Cathegory's json
    Ads = Cathegory_JSON["Ads"]
    Ad = Ads[AdNumber]
    print(f"Message_JSON\n{Ad}")
    Message_Keyword = Ad["Keywords"]
    BaseVariable_Status = Ad["Plan"]

    if BaseVariable_Status == "BASE":
        BaseVariable_Status = True
    else:
        BaseVariable_Status = False

    return Ad, AdNumber, BaseVariable_Status, Message_Keyword # Returns the Ad json (1), AdNumber (2), BaseVariable_Status (3) 

def Post_Message(Cathegory_JSON, AccountToken, Ad_JSON, Account_Cathegory, Account_Number): # Posts the ads in the channels 
    BadRequest = False
    Unauthorized = False
    ErrorLog = []
    Content = Ad_JSON["Content"]
    URLs_JSON = Cathegory_JSON["URLs"] # Gets the IDs of the channels using the JSON
    for json in URLs_JSON:
        time.sleep(random.randint(3,5))
        channel_info = json["channel"]
        guild_info = json["guild"]
        channel_id = channel_info["id"]
        URL = f"https://discord.com/api/channels/{channel_id}/messages"
        headers = {
            "Authorization": AccountToken,
            "Content-Type": "application/json"
        }
        params = {
            "content": Content,
        }
        response = requests.post(URL, headers=headers, json=params) # Posts the Ad in all of the channels using Token

        status_code = response.status_code
        if status_code != 200:
            message_JSON = {
                "guild-name": guild_info["name"],
                "guild-id": guild_info["id"],
                "channel-name": channel_info["name"],
                "channel-id": channel_info["id"],
                "status-code": status_code
                            }
            ErrorLog.append(message_JSON)
        if status_code == 401:
            Unauthorized = True
        elif status_code == 400:
            BadRequest = True
    print(f"DETAILED ERROR LOG:, {ErrorLog}\n\n")
    if Unauthorized == True:
        ErrorLog = f"Unauthorized {Account_Cathegory} | {Account_Number} <@1148657062599983237>"
    # if BadRequest == True:
    #     ErrorLog = f"Bad Request {Account_Cathegory} | {Account_Number}"
    return ErrorLog # Returns a JSON of all the Errors (Status code not 200)
 
def Report_System(ServerCathegory, AccountName, ErrorLog=None, Ad=None, Skipping=False): # Posts a message to the main report channel
    if Skipping == True:
        Content = f"**{ServerCathegory}** | Cathegory\n**{AccountName}** | Account\n\nIt wasnt 6 hours yet - **skipping posting**"
    else:
        if len(ErrorLog) > 0:
            if isinstance(ErrorLog, str):
                Content = ErrorLog
            else:
                NewErrorLog = ""
                number = 1
                for error in ErrorLog:
                    guild_name = error["guild-name"]
                    guild_id = error["guild-id"]
                    channel_name = error["channel-name"]
                    channel_id = error["channel-id"]
                    status_code = error["status-code"]
                    description = f"{number}.  **{status_code}** | {guild_name} ({guild_id})\n-# Channel: {channel_name} ({channel_id})"
                    NewErrorLog = f"{NewErrorLog}\n{description}"
                    number += 1
                Content = (f"**{ServerCathegory}** | Cathegory\n**{AccountName}** | Account\n\n**Errors:**\n{NewErrorLog}\nAd Content:\n\n`{Ad['Content'][:200]}`")
        else:
            Content = ("All Ads posted successfully.")
    PostingChannelURL = f"https://discord.com/api/channels/{PostingChanenelID}/messages"
    Headers = {
        "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    Content = {"content": Content}
    response = requests.post(PostingChannelURL, headers=Headers, json=Content)
    if response.status_code == 200:
        message = "Posting report sent successfully."
    else:
        message = f"Failed to send posting report. Text: {response.text}"
    return message

def Report_Customer(Ad_JSON): # Sends a Report message to the Customer
    AdContent = Ad_JSON["Content"]
    AdPlan = Ad_JSON["Plan"]
    PostingsLeft = Ad_JSON["PostingsLeft"]-1 # Gets all the info from the JSON
    TicketID = Ad_JSON["TicketID"]
    
    if PostingsLeft == 0:
        ReportContent = (f"Ad Plan: {AdPlan}\nAd: `{AdContent[:200]}...`\nYour ad has completed all its posts. <@1148657062599983237>")
    elif PostingsLeft >= 0:
        ReportContent = (f"Ad Plan: {AdPlan}\nAd: `{AdContent[:200]}...`\nPostings Left: {PostingsLeft} (Approximitely {PostingsLeft*50} posts left.)")
    else:
        ReportContent = "There is something wrong with ticket report. Pakoego will fix soon <@1148657062599983237>" 

    headers = {
        "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    CustomerChannelURL = f"https://discord.com/api/channels/{TicketID}/messages"
    Content = {"content": ReportContent}
    response = requests.post(CustomerChannelURL, headers=headers, json=Content)
    print("Message to the CUSTOMER CHANNEL posted with status code:", response.status_code)
    if response.status_code == 200:
        message = "Customer report sent successfully."
    else:
        message = f"Failed to send customer report. Text: {response.text}"
    return message

def Update_Postings(Cathegories, Ad_PLACE,Cathegory_Place, Message_Keyword, Server_ads_data): # Edits the amount of postings left
    print(Cathegory_Place, Ad_PLACE)
    ads = Cathegories[Cathegory_Place]["Ads"]
    status_codes = None
    for ad in ads:
        if ad["Keywords"] == Message_Keyword:
            print("Found the ad to update postings left", ad)
            index = ads.index(ad)
            Old_Postings = Cathegories[Cathegory_Place]["Ads"][ads.index(ad)]["PostingsLeft"]
            New_Postings = Old_Postings - 1
            Cathegories[Cathegory_Place]["Ads"][ads.index(ad)]["PostingsLeft"] = New_Postings
            print(f"Changing postings from {Old_Postings} to {New_Postings}")
            if New_Postings <= 0:
                print("Posting is finished. Replacing with base variable.....")
                Cathegories[Cathegory_Place]["Ads"][ads.index(ad)] = Pick_BaseVariable(Server_ads_data,Cathegories[Cathegory_Place]["Cathegory"])
                print(f"Base variable:\n\n{Cathegories[Cathegory_Place]["Ads"][index]}")
                status_codes = Update_Notion([Ad_PLACE + 1], "_________", Cathegories[Cathegory_Place]["Cathegory"]) # Updates Notion

    return Cathegories, status_codes


def Update_Notion(WhichVariables, Keywords, Cathegory):
    if Cathegory == "RoTech":
        NOTION_DATABASE_ID = NOTION_DATABASE_ID_LIST[0]
    elif Cathegory == "Aviation":
        NOTION_DATABASE_ID = NOTION_DATABASE_ID_LIST[1]
    elif Cathegory == "Advertising":
        NOTION_DATABASE_ID = NOTION_DATABASE_ID_LIST[2]
    elif Cathegory == "Gaming":
        NOTION_DATABASE_ID = NOTION_DATABASE_ID_LIST[3]
    else:
        NOTION_DATABASE_ID = "2d90bcea8f4080d9a67fd07874bbcb61"
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    headers = {
            'Authorization': 'Bearer ' + NOTION_API_KEY,
            'Content-Type': 'application/json',
            'Notion-Version': '2022-06-28',
        }
    data = {
    "sorts": [{
        "property": "Name",
        "direction": "ascending"
    }]
    }
    response = requests.post(url, headers=headers, json=data)

    data = response.json()
    results = data["results"]
    status_codes = []
    for variable in WhichVariables:
        page = results[variable - 1]
        page_id = page["id"]
        new_name = f"{variable} | {Keywords}"

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

def Pick_BaseVariable(Server_ads_data,Cathegory_Name):
    for variable in Server_ads_data:
            Cathegory = variable["Cathegory"]
            if Cathegory_Name == Cathegory:
                index = Server_ads_data.index(variable)     
                BaseVariable_Json = Server_ads_data[index]["Ads"][random.randint(0, len(variable["Ads"])-1)]
                return BaseVariable_Json
def main():
    Cathegories_data, Cathegories_file_name, Report_Message_Gist_GET_1 = Get_Gist(Cathegories_gist_ID)
    Tracker_data, Tracker_file_name, Report_Message_Gist_GET_2 = Get_Gist(Tracker_gist_ID)
    AdNumber, Cathegory_Name, Cathegory_JSON, Cathegory_Place, Account_Number, Tracker_data_New, Base_Variable_Check = Get_Data(Cathegories_data, Tracker_data) # Picks the server and account
    Account_Token, Account_Name = Choose_Accounts(Accounts_data, Cathegory_Name, Account_Number) # Picks the account token and name
    Message_JSON, Message_Place, BaseVariable_Status, Message_Keyword = Pick_Ad(Cathegory_JSON, AdNumber) # Picks the Ad to post
    Server_ads_data, Server_ads_file_name, Report_Message_Gist_GET_3 = Get_Gist(Server_ads_gist_ID)
    if BaseVariable_Status == True: 
        if Base_Variable_Check == True:
            Tracker_data_New["Base-Variable"][Cathegory_Place][Cathegory_Name] += 1
            Message_JSON = Pick_BaseVariable( Server_ads_data,Cathegory_Name) # Picks a BASE variable Ad
            ErrorLog = Post_Message(Cathegory_JSON, Account_Token, Message_JSON, Cathegory_Name, Account_Number) # Posts the Ad
            Report_Message_System = Report_System(ErrorLog, Cathegory_Name, Account_Name, Message_JSON) # Handles any posting
            Update_Gist(Tracker_gist_ID, Tracker_data_New, "tracker.json")
            
        else:
            Report_Message_System = Report_System(ServerCathegory=Cathegory_Name, AccountName=Account_Name, Skipping=True)
        print(f"{Report_Message_System}\n {Report_Message_Gist_GET_1, Report_Message_Gist_GET_2}")
    elif BaseVariable_Status == False:
        ErrorLog = Post_Message(Cathegory_JSON, Account_Token, Message_JSON, Cathegory_Name, Account_Number) # Posts the Ad
        Report_Message_System = Report_System(ErrorLog, Cathegory_Name, Account_Name, Message_JSON) # Handles any posting
        Report_Message_Customer = Report_Customer(Message_JSON) # Sends a report to the customer
        Cathegories, Report_Notion_Update = Update_Postings(Cathegories_data, Message_Place, Cathegory_Place, Message_Keyword, Server_ads_data) # Edits the amount
        Report_Message_Gist_PATCH = Update_Gist(Cathegories_gist_ID,Cathegories, "Cathegories.json")
        print(f"/{Report_Message_Customer}\n {Report_Message_System}\n {Report_Message_Gist_GET_1}\n {Report_Message_Gist_GET_2}\n {Report_Message_Gist_PATCH}\n {Report_Notion_Update}")

    else:
        print("Something is wrong with base variable status", BaseVariable_Status)
    
main()

