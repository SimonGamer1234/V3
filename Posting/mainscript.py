import requests 
import json
import time
import random
import os

ACCOUNTS = json.loads(os.getenv("ACCOUNTS"))

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

SERVER_ADS = json.loads(os.getenv("SERVER_ADS"))

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

Cathegories = json.loads(os.getenv("CATHEGORIES")) # All the cathegories

TrackerFile = "Posting/tracker.json"

PostingChanenelID = 1429473972096995370


def ServersPicker(): # Chooses in which servers it will post with which account
    with open(TrackerFile, 'r') as f:
       data = json.load(f)
       Accounts = data["Accounts"]
       for Account in Accounts:
          if Account["Cathegory"] == Cathegory_JSON["Cathegory"]:
              AdNumber = Account["AdNumber"]
    Cathegory_PLACE = data["Number"]
    Plan = Accounts[Cathegory_PLACE]
    Cathegory_NAME = Cathegories[Cathegory_PLACE]["Cathegory"]
    AccountNumber = Plan["AccountNumber"]
    with open(TrackerFile, 'w') as f: # Edits the Cathegory tracker
        if Cathegory_PLACE + 1 >= 4:
            data["Number"] = 0
        else:
            data["Number"] = Cathegory_PLACE + 1
        json.dump(data, f, indent=4)
    with open(TrackerFile, 'w') as f: # Edits the Account tracker
        if AccountNumber + 1 >= len(ACCOUNTS): 
            Plan["AccountNumber"] = 0
        else:
            Plan["AccountNumber"] = AccountNumber + 1
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
      if AdNumber + 1 >= len(Ads):
          Accounts["AdNumber"] = 0
      else:
          Accounts["AdNumber"] = AdNumber + 1
      json.dump(data, f, indent=4)

  return Ad, AdNumber, Ads # Returns the Ad json (1), AdNumber (2), List of all Ads in the cathegory (3) 

def PostAd(Cathegory_JSON, AccountToken, Ad_JSON): # Posts the ads in the channels 
    ErrorLog = []
    URLs = Cathegory_JSON["URLs"] # Gets the IDs of the channels using the JSON
    for URL in URLs:
        headers = {
            "Authorization": {AccountToken},
            "Content-Type": "application/json"
        }
        params = {
            "content": Ad_JSON["Content"],
        }
        response = requests.post(URL, headers=headers, json=params) # Posts the Ad in all of the channels using Token

        StatusCode = response.status_code
        if StatusCode != 200:
            ErrorLog.append({
                "ID":URL, 
                "StatusCode":StatusCode
                })
    return ErrorLog # Returns a JSON of all the Errors (Status code not 200)
 
def HandlePostingErrors(ErrorLog, ServerCathegory, AccountName): # Posts a message to the main report channel
    if len(ErrorLog) > 0:
        Content = (f"Cathegory:{ServerCathegory}\nAccount:{AccountName}\nErrors:\n{ErrorLog}")
    else:
        Content = ("All Ads posted successfully.")
    PostingChannelURL = f"https://discord.com/api/channels/{PostingChanenelID}/messages"
    Headers = {
        "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    Content = {"content": Content}
    response = requests.post(PostingChannelURL, headers=Headers, json=Content)
    print("Message to the ERROR CHANNEL posted with status code:", response.status_code) #

def CustomerReport(Ad_JSON): # Sends a Report message to the Customer
    AdContent = Ad_JSON["Content"]
    AdPlan = Ad_JSON["Plan"]
    PostingsLeft = Ad_JSON["PostingsLeft"] # Gets all the info from the JSON
    TicketID = Ad_JSON["TicketID"]
    
    if PostingsLeft == 0:
        ReportContent = (f"Ad Plan: {AdPlan}\nTicket ID: {PostingsLeft} Ad: `{AdContent}`\nYour ad has completed all its posts.")
    elif PostingsLeft >= 0:
        ReportContent = (f"Ad Plan: {AdPlan}\nTicket ID: {TicketID}\nAd: `{AdContent}`\nPostings Left: {PostingsLeft}")
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

def EditingPostingsLeft(Ad_PLACE,Cathegory_PLACE): # Edits the amount of postings left
    NewPostingsLeft = Cathegories[Cathegory_PLACE]["Ads"][Ad_PLACE]["PostingsLeft"] - 1 # Decreases the Postings by 1
    if NewPostingsLeft == 0:
        Cathegories[Cathegory_PLACE]["Ads"][Ad_PLACE] = SERVER_ADS[random.randint(0, len(SERVER_ADS))] # Replaces the Ad with the BASE_AD - randomly choosed from the SERVER_ADS
    headers = {
    'Accept': 'application/vnd.github+json',
    'Authorization': 'Bearer '+ GITHUB_TOKEN,
    'X-GitHub-Api-Version': '2022-11-28',
    'Content-Type': 'application/x-www-form-urlencoded',
    }

    data = {"value":Cathegories}
    url  = f"https://api.github.com/repos/SimonGamer1234/V3/actions/variables/Cathegories"
    response = requests.patch(url, headers=headers, data=data) # Updates the GitHub variable
    print("GitHub Variable updated with status code:", response.status_code)


def main():
    Cathegory_NAME, Cathegory_PLACE, AccountNumber = ServersPicker() # Picks the server and account
    AccountToken, AccountName = DifferAccounts(Cathegory_NAME, AccountNumber) # Picks the account token and name
    Cathegory_JSON = Cathegories[Cathegory_PLACE] # Gets the Cathegory JSON
    Ad_JSON, Ad_PLACE, BaseVariable_Status = AdPicker(Cathegory_JSON) # Picks the Ad to post
    if BaseVariable_Status == True:
        Ad_JSON = random.randint(0, len(SERVER_ADS))
    elif BaseVariable_Status == False:
        ErrorLog = PostAd(Cathegory_JSON, AccountToken, Ad_JSON) # Posts the Ad
        HandlePostingErrors(ErrorLog, Cathegory_NAME, AccountName) # Handles any posting
        CustomerReport(Ad_JSON) # Sends a report to the customer
        EditingPostingsLeft(Ad_PLACE, Cathegory_PLACE) # Edits the amount
main()

