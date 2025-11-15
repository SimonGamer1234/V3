from flask import Flask, request, jsonify
import json
import os
import requests


GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID_LIST = os.getenv("NOTION_DATABASE_ID_LIST")

app = Flask(__name__)
@app.route('/api/data', methods=['POST'])

def main():
    Cathegories = Get_Cathegories_Variable()
    Cathegories_New, Keywords, WhichVariables, Cathegory = handle_data(Cathegories)
    Update_GitHub(Cathegories_New)
    Update_Notion(WhichVariables, Keywords, Cathegory)
    return 200


def Get_Cathegories_Variable():
    url = f'https://api.github.com/repos/SimonGamer1234/V3/actions/variables/CATHEGORIES'
    headers = {
            'Accept': 'application/vnd.github+json',
            'Authorization': f'Bearer {GITHUB_TOKEN}',
            'X-GitHub-Api-Version': '2022-11-28',
        }
    response = requests.get(url, headers=headers)
    data = response.json()
    CATHEGORIES = data["value"]
    CATHEGORIES = json.loads(CATHEGORIES)
    return CATHEGORIES  

def handle_data(CATHEGORIES):
    data = request.get_json()
    Content = data.get('Content')
    Plan = data.get('Plan')
    TimeSpan = data.get("TimeSpan")
    TicketID = data.get('TicketID')
    Keywords = data.get('Keywords')
    WhichVariables = data.get('WhichVariables')
    Cathegory = data.get('Cathegory')
    
    Content = Content.replace("<NEWLINE>", "\n")

    if Plan == "Basic":
        PostingsLeft = TimeSpan * 3
    elif Plan == "Pro":
        PostingsLeft = TimeSpan * 6


    Message = {"Content": Content,"Plan": Plan,"PostingsLeft": PostingsLeft,"TicketID": TicketID,}
    for WhichVariable in WhichVariables:
        number = -1
        for cathegory in CATHEGORIES:
            number += 1
            if cathegory["Cathegory"] == Cathegory:
                CATHEGORIES[number]["Ads"][WhichVariable-1] = Message
    print(data)
    return CATHEGORIES, Keywords, WhichVariables, Cathegory

def Update_GitHub(CATHEGORIES):
    headers = {
    'Accept': 'application/vnd.github+json',
    'Authorization': 'Bearer '+ GITHUB_TOKEN,
    'X-GitHub-Api-Version': '2022-11-28',
    'Content-Type': 'application/json',
    }

    data = {"value":json.dumps(CATHEGORIES)}
    url  = f"https://api.github.com/repos/SimonGamer1234/V3/actions/variables/Cathegories"
    response = requests.patch(url, headers=headers, json=data) # Updates the GitHub variable
    print("GitHub Variable updated with status code:", response.status_code, response.text)


def Update_Notion(WhichVariables, Keywords, Cathegory):
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

@app.route('/cron', methods=['GET'])
def cron():
    return "Cron job executed", 200



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)