import requests 
import json
import time
import random
import os

ACCOUNTS = os.getenv("ACCOUNTS")
ACCOUNTS = json.loads(ACCOUNTS)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

SERVER_ADS = json.loads(os.getenv("BASE_AD"))

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

RoTech = os.getenv("RoTech")
RoTech = json.loads(RoTech)

Gaming = os.getenv("Gaming")
Gaming = json.loads(Gaming)

Aviation = os.getenv("Aviation")
Aviation = json.loads(Aviation)

Advertising = os.getenv("Advertising")
Advertising = json.loads(Advertising)

TrackerFile = "tracker.json"

PostingChanenelID = 1429473972096995370
            
def ServersPicker():
    with open(TrackerFile, 'r') as f:
        data = json.load(f)
    accounts = data["Accounts"]
    number = data["Number"]
    Plan = accounts[number]
    if number == 1:
        ServerCathegory = RoTech
    elif number == 2:
        ServerCathegory = Aviation
    elif number == 3:
        ServerCathegory = Advertising
    elif number == 4:
        ServerCathegory = Gaming
    else:
        print("Error: Unknown Cathegory")
        return None, None
    AccountNumber = Plan["AccountNumber"]
    with open(TrackerFile, 'w') as f:
        if number + 1 >= len(accounts):
            data["Number"] = 0
        else:
            data["Number"] = number + 1
        json.dump(data, f, indent=4)
    with open(TrackerFile, 'w') as f:
        if AccountNumber + 1 >= len(ACCOUNTS):
            Plan["AccountNumber"] = 0
        else:
            Plan["AccountNumber"] = AccountNumber + 1
        json.dump(data, f, indent=4)
    
    return ServerCathegory, AccountNumber

def DifferAccounts(ServerCathegory, AccountNumber):
    for account in ACCOUNTS:
        cathegory = account["Cathegory"]
        if cathegory == ServerCathegory["Cathegory"]:
            if account["AccountNumber"] == AccountNumber:
                AccountToken = account["Token"]
                AccountName = account["Name"]
                return AccountToken, AccountName
    print("Error: Account not found")
    return None, None
            

def AdPicker(Servers):
  Ads = Servers["Ads"]
  with open(TrackerFile, 'r') as f:
      data = json.load(f)
      Accounts = data["Accounts"]
      AdNumber = Accounts["AdNumber"]
  Ad = Ads[AdNumber]
  with open(TrackerFile, 'w') as f:
      if AdNumber + 1 >= len(Ads):
          Accounts["AdNumber"] = 0
      else:
          Accounts["AdNumber"] = AdNumber + 1
      json.dump(data, f, indent=4)
  return Ad, AdNumber, Ads

def PostAd(Servers, AccountToken, Ad):
    ErrorLog = []
    URLs = Servers["URLs"]
    for URL in URLs:
        headers = {
            "Authorization": {AccountToken},
            "Content-Type": "application/json"
        }
        params = {
            "content": Ad["Content"],
        }
        response = requests.post(URL, headers=headers, json=params)

        StatusCode = response.status_code
        if StatusCode != 200:
            ErrorLog.append({
                "ID":URL, 
                "StatusCode":StatusCode
                })
    return ErrorLog

def HandlePostingErrors(ErrorLog, ServerCathegory, AccountName):
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
    print("Message to the ERROR CHANNEL posted with status code:", response.status_code)

def CustomerReport(Ad):
    AdContent = Ad["Content"]
    AdPlan = Ad["Plan"]
    PostingsLeft = Ad["PostingsLeft"]
    TicketID = Ad["TicketID"]
    
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

def EditingPostingsLeft(Ad, Ads, ServerCathegory):
    NewAds = Ads[Ad]["PostingsLeft"] - 1
    headers = {
    'Accept': 'application/vnd.github+json',
    'Authorization': 'Bearer '+ GITHUB_TOKEN,
    'X-GitHub-Api-Version': '2022-11-28',
    'Content-Type': 'application/x-www-form-urlencoded',
    }

    data = {"value":NewAds}
    url  = f"https://api.github.com/repos/SimonGamer1234/V3/actions/variables/{ServerCathegory}"
    response = requests.patch(url, headers=headers, data=data)
    print("GitHub Variable updated with status code:", response.status_code)


def main():
    ServerCathegory, AccountNumber = ServersPicker()
    if ServerCathegory is None or AccountNumber is None:
        print("Error in picking server cathegory or account number.")
        return

    AccountToken, AccountName = DifferAccounts(ServerCathegory, AccountNumber)
    if AccountToken is None or AccountName is None:
        print("Error in differentiating accounts.")
        return

    Ad, AdNumber, Ads = AdPicker(ServerCathegory)
    if Ad is None:
        print("Error in picking ad.")
        return

    ErrorLog = PostAd(ServerCathegory, AccountToken, Ad)
    HandlePostingErrors(ErrorLog, ServerCathegory["Cathegory"], AccountName)
    CustomerReport(Ad)
    EditingPostingsLeft(AdNumber, Ads, ServerCathegory["Cathegory"])
