from flask import Flask, request, jsonify
import json
import os
import requests


CATHEGORIES = json.loads(os.getenv("CATHEGORIES"))


app = Flask(__name__)
@app.route('/api/data', methods=['POST'])
def handle_data():
    data = request.get_json()
    Content = data.get('Content')
    Plan = data.get('Plan')
    PostingsLeft = data.get('PostedBefore')
    TicketID = data.get('TicketID')
    Keywords = data.get('Keywords')
    WhcihVariables = data.get('WhichVariables')
    Cathegory = data.get('Cathegory')
    
    Content = Content.replace("<NEWLINE>", "\n")


    Message = {
        "Content": Content,
        "Plan": Plan,
        "PostingsLeft": PostingsLeft,
        "TicketID": TicketID,
    }
    for WhichVariable in WhcihVariables:
        for cathegory in CATHEGORIES:
            if cathegory["Cathegory"] == Cathegory:
                CATHEGORIES[Cathegory]["Ads"][WhichVariable-1] = Message
    return CATHEGORIES, Keywords

def Update_GitHub(CATHEGORIES):
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    headers = {
    'Accept': 'application/vnd.github+json',
    'Authorization': 'Bearer '+ GITHUB_TOKEN,
    'X-GitHub-Api-Version': '2022-11-28',
    'Content-Type': 'application/x-www-form-urlencoded',
    }

    data = {"value":CATHEGORIES}
    url  = f"https://api.github.com/repos/SimonGamer1234/V3/actions/variables/Cathegories"
    response = requests.patch(url, headers=headers, data=data) # Updates the GitHub variable
    print("GitHub Variable updated with status code:", response.status_code)


def Update_Norion(WhichVariable, Keywords, Cathegory):
    NOTION_API_KEY = os.getenv("NOTION_API_KEY")
    NOTION_DATABASE_ID_LIST = os.getenv("NOTION_DATABASE_ID_LIST")
    if Cathegory == "RoTech":
        NOTION_DATABASE_ID = NOTION_DATABASE_ID_LIST.split(",")[0]
    elif Cathegory == "Aviation":
        NOTION_DATABASE_ID = NOTION_DATABASE_ID_LIST.split(",")[1]
    elif Cathegory == "Advertising":
        NOTION_DATABASE_ID = NOTION_DATABASE_ID_LIST.split(",")[2]
    elif Cathegory == "Gaming":
        NOTION_DATABASE_ID = NOTION_DATABASE_ID_LIST.split(",")[3]
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

    data = response.json()
    results = data["results"]
    Titles = []
    for result in results:
        Properties = result["properties"]
        Name = Properties["Name"]
        Title1 = Name["title"]

        Title = Title1[0]
        PlainText = Title["plain_text"]
        Titles.append(PlainText)
    for VariablNumber in WhichVariable:
        Name = f"{WhichVariable} | {Keywords}"
        results[VariablNumber-1]["properties"]["Name"]["title"][0]["plain_text"] = Name
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}"
    headers = {
                'Authorization': 'Bearer ' + NOTION_API_KEY,
                'Content-Type': 'application/json',
                'Notion-Version': '2022-06-28',
            }
    data = {results}
    response = requests.patch(url, headers=headers, json=data)
    print("Notion updated with status code:", response.status_code)