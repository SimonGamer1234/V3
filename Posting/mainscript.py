import requests 
import json
import time
import random
import os

ACCOUNTS = json.loads(os.getenv("ACCOUNTS"))

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

GIST_ID = os.getenv("GIST_ID")
SERVER_ADS = json.loads(os.getenv("SERVER_ADS"))

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN").strip()

NOTION_API_KEY = os.getenv("NOTION_API_KEY")

NOTION_DATABASE_ID_LIST = os.getenv("NOTION_DATABASE_ID_LIST").split(",")

Cathegories = json.loads(os.getenv("CATHEGORIES")) # All the cathegories

TrackerFile = "Posting/tracker.json"

PostingChanenelID = 1429473972096995370

def Get_Cathegories_From_Gist():
    url = f"https://api.github.com/gists/{GIST_ID}"
    headers = {
        'Authorization': 'Bearer ' + GITHUB_TOKEN,
        'Content-Type': 'application/json',
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        message = "Gist fetched successfully."
        gist_data = response.json()
        file_content = gist_data['files']['Cathegories.json']['content']
        Cathegories = json.loads(file_content)
        return Cathegories, message
    else:
        message = f"Failed to fetch gist. Status code: {response.status_code}"
        return None, message
    

def Update_Cathegories_Gist(Cathegories):
    url = f"https://api.github.com/gists/{GIST_ID}"
    headers = {
        'Authorization': 'Bearer ' + GITHUB_TOKEN,
        'Content-Type': 'application/json',
    }
    data = {
        "files": {
            "Cathegories.json": {
                "content": json.dumps(Cathegories, indent=4)
            }
        }
    }
    response = requests.patch(url, headers=headers, json=data)
    if response.status_code == 200:
        message = "Gist updated successfully."
    else:
        message = f"Failed to update gist. Status code: {response.status_code}"
    return message

def Get_Data(Cathegories): # Chooses in which servers it will post with which account
    
    with open(TrackerFile, 'r') as f:
        data = json.load(f)
        Cathegory_PLACE = data["Number"]
        Accounts = data["Accounts"]
        print(f"Cathegory Number: {Cathegory_PLACE}")

    Cathegory_JSON = Cathegories[Cathegory_PLACE]
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
    
    return Cathegory_NAME, Cathegory_JSON, Cathegory_PLACE, AccountNumber # Returns the NAME and the PLACE of the Cathegory and the NUMBER of the account in the account list.

def Choose_Accounts(Cathegory_NAME, AccountNumber): # Uses the Cathegory name to find the right accounts, chooses one according to the AccountNumber
    for account in ACCOUNTS:
        cathegory = account["Cathegory"]
        if Cathegory_NAME in cathegory:
            if account["AccountNumber"] == AccountNumber:
                AccountToken = account["Token"]
                AccountName = account["Name"]
                return AccountToken, AccountName # Returns the TOKEN and the USERNAME of the account - !maybe change to ID later!
    
    print("Error: Account not found")
    return None, None
            

def Pick_Ad(Cathegory_JSON): # Uses the AdNumber in tracker.json to pick the ad from the list of ads in the Cathegory's json
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

def Post_Message(Cathegory_JSON, AccountToken, Ad_JSON, Account_Cathegory, Account_Number): # Posts the ads in the channels 
    BadRequest = False
    Unauthorized = False
    ErrorLog = []
    Content = Ad_JSON["Content"]
    print(f"Message:\n{Content}")
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
            "content": Content,
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
 
def Report_System(ErrorLog, ServerCathegory, AccountName, Ad): # Posts a message to the main report channel
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
        print("There is something wrong with ticket report. Pakoego will fix soon")

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

def Update_Postings(Ad_PLACE,Cathegory_PLACE): # Edits the amount of postings left
    print(Cathegory_PLACE, Ad_PLACE)
    ads = Cathegories[Cathegory_PLACE]["Ads"]
    for ad in ads:
        if ad["Keywords"] == ads[Ad_PLACE]["Keywords"]:
            print("Found the ad to update postings left", ad)
            index = Cathegories[Cathegory_PLACE]["Ads"][ads.index(ad)]
            Old_Postings = Cathegories[Cathegory_PLACE]["Ads"][ads.index(ad)]["PostingsLeft"]
            New_Postings = Old_Postings - 1
            Cathegories[Cathegory_PLACE]["Ads"][ads.index(ad)]["PostingsLeft"] = New_Postings
            print(f"Changing postings from {Old_Postings} to {New_Postings}")
            if New_Postings == 0:
                print("Posting is finished. Replacing with base variable.....")
                Cathegories[Cathegory_PLACE]["Ads"][ads.index(ad)] = Pick_BaseVariable(Cathegories[Cathegory_PLACE]["Cathegory"])
                print(f"Base variable:\n\n{Cathegories[Cathegory_PLACE]["Ads"][index]}")
                status_codes = Update_Notion([Ad_PLACE + 1], "_________", Cathegories[Cathegory_PLACE]["Cathegory"]) # Updates Notion

    Report = Update_Cathegories_Gist(Cathegories) # Updates the Gist with new postings left
    return Report, status_codes


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

def Pick_BaseVariable(Cathegory_Name):
    for variable in SERVER_ADS:
            Cathegory = variable["Cathegory"]
            if Cathegory_Name == Cathegory:
                index = SERVER_ADS.index(variable)     
                BaseVariable_Json = SERVER_ADS[index]["Ads"][random.randint(0, len(variable["Ads"])-1)]
                return BaseVariable_Json
def main():
    Cathegories, Report_Message_Gist = Get_Cathegories_From_Gist() # Gets the Cathegories from Gist
    Cathegory_Name, Cathegory_JSON, Cathegory_Place, Account_Number = Get_Data(Cathegories) # Picks the server and account
    Account_Token, Account_Name = Choose_Accounts(Cathegory_Name, Account_Number) # Picks the account token and name
    Message_JSON, Message_Place, BaseVariable_Status = Pick_Ad(Cathegory_JSON) # Picks the Ad to post
    if BaseVariable_Status == True: 
        print("Base Variable is true")
        Message_JSON = Pick_BaseVariable(Cathegory_Name) # Picks a BASE variable Ad
        ErrorLog = Post_Message(Cathegory_JSON, Account_Token, Message_JSON, Cathegory_Name, Account_Number) # Posts the Ad
        Report_Message_System = Report_System(ErrorLog, Cathegory_Name, Account_Name, Message_JSON) # Handles any posting
        print(f"{Report_Message_System}\n {Report_Message_Gist}")
    elif BaseVariable_Status == False:
        print("Base Variable is false")
        ErrorLog = Post_Message(Cathegory_JSON, Account_Token, Message_JSON, Cathegory_Name, Account_Number) # Posts the Ad
        Report_Message_System = Report_System(ErrorLog, Cathegory_Name, Account_Name, Message_JSON) # Handles any posting
        Report_Message_Customer = Report_Customer(Message_JSON) # Sends a report to the customer
        Report_Message_Update, Report_Notion_Update = Update_Postings(Message_Place, Cathegory_Place) # Edits the amount
        print(f"/{Report_Message_Customer}\n {Report_Message_System}\n {Report_Message_Gist}\n {Report_Message_Update}\n {Report_Notion_Update}")
    else:
        print("Something is wrong with base variable status", BaseVariable_Status)
    
main()

