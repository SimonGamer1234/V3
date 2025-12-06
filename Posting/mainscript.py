import requests 
import json
import time
import random
import os

ACCOUNTS = json.loads(os.getenv("ACCOUNTS"))

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

SERVER_ADS = json.loads(os.getenv("SERVER_ADS"))

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN").strip()

NOTION_API_KEY = os.getenv("NOTION_API_KEY")

NOTION_DATABASE_ID_LIST = os.getenv("NOTION_DATABASE_ID_LIST").split(",")

Cathegories = json.loads(os.getenv("CATHEGORIES")) # All the cathegories

TrackerFile = "Posting/tracker.json"

PostingChanenelID = 1429473972096995370


def ServersPicker(): # Chooses in which servers it will post with which account
    
    with open(TrackerFile, 'r') as f:
        data = json.load(f)
        Cathegory_PLACE = data["Number"]
        Accounts = data["Accounts"]
        print(f"Cathegory Number: {Cathegory_PLACE}")

    Plan = Accounts[Cathegory_PLACE]
    Cathegory_NAME = Cathegories[Cathegory_PLACE]["Cathegory"]
    AccountNumber = Plan["AccountNumber"]
    with open(TrackerFile, 'w') as f: # Edits the Cathegory tracker
        if Cathegory_PLACE + 1 >= 4:
            data["Number"] = 0
        else:
            data["Number"] = Cathegory_PLACE + 1
        if AccountNumber == 4: 
            Plan["AccountNumber"] = 1
        else:
            Plan["AccountNumber"] = AccountNumber + 1
        data["Accounts"][Cathegory_PLACE] = Plan
        json.dump(data, f, indent=4)
    
    return Cathegory_NAME, Cathegory_PLACE, AccountNumber # Returns the NAME and the PLACE of the Cathegory and the NUMBER of the account in the account list.

def DifferAccounts(Cathegory_NAME, AccountNumber): # Uses the Cathegory name to find the right accounts, chooses one according to the AccountNumber
    for account in ACCOUNTS:
        cathegory = account["Cathegory"]
        if Cathegory_NAME in cathegory:
            if account["AccountNumber"] == AccountNumber:
                AccountToken = account["Token"]
                AccountName = account["Name"]
                return AccountToken, AccountName # Returns the TOKEN and the USERNAME of the account - !maybe change to ID later!
    
    print("Error: Account not found")
    return None, None
            

def AdPicker(Cathegory_JSON): # Uses the AdNumber in tracker.json to pick the ad from the list of ads in the Cathegory's json
  Ads = Cathegory_JSON["Ads"]
  with open(TrackerFile, 'r') as f: # Gets the AdNumber
      data = json.load(f)
      Accounts = data["Accounts"]
      for Account in Accounts:
          if Account["Cathegory"] == Cathegory_JSON["Cathegory"]:
              AdNumber = Account["AdNumber"]
          
  Ad = Ads[AdNumber]
  BaseVariable_Status = Ad["Plan"]
  if BaseVariable_Status == "BASE":
    BaseVariable_Status = True
  else:
    BaseVariable_Status = False
  with open(TrackerFile, 'w') as f: # Updates -||-
      for Account in Accounts:
          if Account["Cathegory"] == Cathegory_JSON["Cathegory"]:
              AdNumber = Account["AdNumber"]
              if AdNumber + 1 >= len(Ads):
                  Account["AdNumber"] = 0
              else:
                  Account["AdNumber"] = AdNumber + 1
      json.dump(data, f, indent=4)

  return Ad, AdNumber, BaseVariable_Status # Returns the Ad json (1), AdNumber (2), BaseVariable_Status (3) 

def PostAd(Cathegory_JSON, AccountToken, Ad_JSON, Account_Cathegory, Account_Number): # Posts the ads in the channels 
    BadRequest = False
    Unauthorized = False
    ErrorLog = []
    ID_JSON = Cathegory_JSON["URLs"] # Gets the IDs of the channels using the JSON
    for json in ID_JSON:
        time.sleep(random.randint(3,5))
        id = json["id"]
        name = json["name"]
        URL = f"https://discord.com/api/channels/{id}/messages"
        headers = {
            "Authorization": AccountToken,
            "Content-Type": "application/json"
        }
        params = {
            "content": Ad_JSON["Content"],
        }
        response = requests.post(URL, headers=headers, json=params) # Posts the Ad in all of the channels using Token

        StatusCode = response.status_code
        if StatusCode != 200:
            ErrorLog.append({
                "ID":id, 
                "StatusCode":StatusCode,
                "ServerName":name
                })
        if StatusCode == 401:
            Unauthorized = True
        elif StatusCode == 400:
            BadRequest = True
    print(f"DETAILED ERROR LOG:, {ErrorLog}\n\n")
    if Unauthorized == True:
        ErrorLog = f"Unauthorized {Account_Cathegory} | {Account_Number} <@1148657062599983237>"
    # if BadRequest == True:
    #     ErrorLog = f"Bad Request {Account_Cathegory} | {Account_Number}"
    return ErrorLog # Returns a JSON of all the Errors (Status code not 200)
 
def HandlePostingErrors(ErrorLog, ServerCathegory, AccountName, Ad): # Posts a message to the main report channel
    NewErrorLog = ""
    for error in ErrorLog:
        NewErrorLog = f"{NewErrorLog}\n{error}"
    if len(ErrorLog) > 0:
        Content = (f"Cathegory:{ServerCathegory}\nAccount:{AccountName}\nErrors:\n{NewErrorLog}\nAd Content:\n`{Ad['Content'][:200]}`")
    else:
        Content = ("All Ads posted successfully.")
    PostingChannelURL = f"https://discord.com/api/channels/{PostingChanenelID}/messages"
    Headers = {
        "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    Content = {"content": Content}
    response = requests.post(PostingChannelURL, headers=Headers, json=Content)
    print("Message to the ERROR CHANNEL posted with status code:", response.status_code, response.text) #
    print(ErrorLog)

def CustomerReport(Ad_JSON): # Sends a Report message to the Customer
    AdContent = Ad_JSON["Content"]
    AdPlan = Ad_JSON["Plan"]
    PostingsLeft = Ad_JSON["PostingsLeft"]-1 # Gets all the info from the JSON
    TicketID = Ad_JSON["TicketID"]
    
    if PostingsLeft == 0:
        ReportContent = (f"Ad Plan: {AdPlan}\nAd: `{AdContent[:200]}...`\nYour ad has completed all its posts. <@1148657062599983237>")
    elif PostingsLeft >= 0:
        ReportContent = (f"Ad Plan: {AdPlan}\nAd: `{AdContent[:200]}...`\nPostings Left: {PostingsLeft} (Approximitely {PostingsLeft*50} posts left.)")
    else:
        print("There is something wrong with ticket report. Pakoego will fix soon")

    headers = {
        "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    CustomerChannelURL = f"https://discord.com/api/channels/{TicketID}/messages"
    Content = {"content": ReportContent}
    response = requests.post(CustomerChannelURL, headers=headers, json=Content)
    print("Message to the CUSTOMER CHANNEL posted with status code:", response.status_code)
    if response.status_code != 200:
        print("There was an error sending the customer report:", response.text)

def EditingPostingsLeft(Ad_PLACE,Cathegory_PLACE): # Edits the amount of postings left
    ads = Cathegories[Cathegory_PLACE]["Ads"]
    for ad in ads:
        print(ad["Keywords"], ads[Ad_PLACE]["Keywords"])
        if ad["Keywords"] == ads[Ad_PLACE]["Keywords"]:
            Cathegories[Cathegory_PLACE]["Ads"][ads.index(ad)]["PostingsLeft"] = Cathegories[Cathegory_PLACE]["Ads"][ads.index(ad)]["PostingsLeft"]-1 
            NewPostingsLeft = Cathegories[Cathegory_PLACE]["Ads"][ads.index(ad)]["PostingsLeft"]
            if NewPostingsLeft == 0:
                Cathegories[Cathegory_PLACE]["Ads"][ads.index(ad)] = Pick_BaseVariable(Cathegories[Cathegory_PLACE]["Cathegory"])
                Update_Notion([Ad_PLACE + 1], "_________", Cathegories[Cathegory_PLACE]["Cathegory"]) # Updates Notion

    headers = {
    'Accept': 'application/vnd.github+json',
    'Authorization': 'Bearer '+ GITHUB_TOKEN,
    'X-GitHub-Api-Version': '2022-11-28',
    'Content-Type': 'application/json',
    }

    data = {"value": json.dumps(Cathegories)}
    url  = f"https://api.github.com/repos/SimonGamer1234/V3/actions/variables/Cathegories"
    response = requests.patch(url, headers=headers, json=data) # Updates the GitHub variable
    print("GitHub Variable updated with status code:", response.status_code, response.text)


def Update_Notion(WhichVariables, Keywords, Cathegory):
    if Cathegory == "RoTech":
        NOTION_DATABASE_ID = NOTION_DATABASE_ID_LIST[0]
    elif Cathegory == "Aviation":
        NOTION_DATABASE_ID = NOTION_DATABASE_ID_LIST[1]
    elif Cathegory == "Advertising":
        NOTION_DATABASE_ID = NOTION_DATABASE_ID_LIST[2]
    elif Cathegory == "Gaming":
        NOTION_DATABASE_ID = NOTION_DATABASE_ID_LIST[3]
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

    print(response.status_code)
    print(url)

    data = response.json()
    results = data["results"]
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
        print("Notion updated with status code:", response.status_code)

def Pick_BaseVariable(Cathegory_Name):
    for variable in SERVER_ADS:
            index = SERVER_ADS.index(variable)
            BASEVARIABLE_NUMBER_Json = SERVER_ADS[index]["Ads"][random.randint(0, len(variable["Ads"])-1)]
            return BASEVARIABLE_NUMBER_Json
def main():
    Cathegory_NAME, Cathegory_PLACE, AccountNumber = ServersPicker() # Picks the server and account
    AccountToken, AccountName = DifferAccounts(Cathegory_NAME, AccountNumber) # Picks the account token and name
    Cathegory_JSON = Cathegories[Cathegory_PLACE] # Gets the Cathegory JSON
    Ad_JSON, Ad_PLACE, BaseVariable_Status = AdPicker(Cathegory_JSON) # Picks the Ad to post
    if BaseVariable_Status == True:
        print("Base Variable is true")
        Ad_JSON = Pick_BaseVariable(Cathegory_NAME) # Picks a BASE variable Ad
        ErrorLog = PostAd(Cathegory_JSON, AccountToken, Ad_JSON, Cathegory_NAME, AccountNumber) # Posts the Ad
        HandlePostingErrors(ErrorLog, Cathegory_NAME, AccountName, Ad_JSON) # Handles any posting
    elif BaseVariable_Status == False:
        print("Base Variable is false")
        ErrorLog = PostAd(Cathegory_JSON, AccountToken, Ad_JSON, Cathegory_NAME, AccountNumber) # Posts the Ad
        HandlePostingErrors(ErrorLog, Cathegory_NAME, AccountName, Ad_JSON) # Handles any posting
        CustomerReport(Ad_JSON) # Sends a report to the customer
        EditingPostingsLeft(Ad_PLACE, Cathegory_PLACE) # Edits the amount
    else:
        print("Something is wrong with base variable status", BaseVariable_Status)
main()

