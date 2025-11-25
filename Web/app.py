from flask import Flask, request, jsonify
import json
import os
import requests


GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID_LIST = os.getenv("NOTION_DATABASE_ID_LIST")

app = Flask(__name__)
@app.route('/api/data', methods=['GET'])

def main():
    Cathegories = Get_Cathegories_Variable()
    Content, Message_Place, Timespan, TicketID, Plan, Cathegory, Keywords = Get_Content()
    Cathegories_New, Keywords, WhichVariables, Cathegory = handle_data(Cathegories, Content, Plan , Timespan, TicketID, Keywords, Message_Place, Cathegory)
    Update_GitHub(Cathegories_New)
    Update_Notion(Message_Place, Keywords, Cathegory)
    return "Success",200


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
def Get_Content():
    finaltext = ""
    annotation_list = [
        {"name": "bold", "symbol": "**"},
        {"name": "italic", "symbol": "*"},
        {"name": "strikethrough", "symbol": "~"},
        {"name": "underline", "symbol": "__"},
        {"name": "code", "symbol": "`"}
    ]

    id = "23f0bcea8f40804fb74dd150116b5cc8"
    url = f"https://api.notion.com/v1/blocks/{id}/children"
    headers = {
        'Authorization': 'Bearer ' + NOTION_API_KEY,
        'Content-Type': 'application/json',
        'Notion-Version': '2022-06-28',
    }

    response = requests.get(url, headers=headers)
    print(response.status_code)
    output = response.json()

    # Loop through each block in the "results"
    for block in output.get("results", []):
        block_type = block["type"]
        rich = block[block_type].get("rich_text", [])

        # Combine all rich text parts in the block
        for part in rich:
            text = part["plain_text"]
            annotation = part["annotations"]

            # apply markdown styles
            for style in annotation_list:
                if annotation.get(style["name"]):
                    text = f"{style['symbol']}{text}{style['symbol']}"

            finaltext += text

        # Add line breaks between blocks
    pageid = "2970bcea8f40802ea360e67b1e008c7a"
    url2 = f"https://api.notion.com/v1/pages/{pageid}"
    response2 = requests.get(url2, headers=headers)
    response2_json = response2.json()
    properties = response2_json["properties"]
    Message_Place = properties["Message Place"]["rich_text"][0]["plain_text"]
    Message_Place = Message_Place.split(",")
    Timespan = properties["Timespan"]["number"]
    TicketID = properties["TicketID"]["rich_text"][0]["plain_text"]
    Plan = properties["Plan"]["select"]["name"]
    Cathegory = properties["Cathegory"]["select"]["name"]
    Keywords = properties["Keywords"]["title"][0]["plain_text"]
    print(finaltext, Message_Place, TicketID, Plan, Cathegory, Keywords)
    return finaltext, Message_Place, Timespan, TicketID, Plan, Cathegory, Keywords

def handle_data(CATHEGORIES, Content, Plan, TimeSpan, TicketID, Keywords, WhichVariables, Cathegory):
        
    print(WhichVariables)
    Content = Content.replace("<NEWLINE>", "\n")

    if Plan == "Basic":
        PostingsLeft = TimeSpan * 3
    elif Plan == "Pro":
        PostingsLeft = TimeSpan * 6


    Message = {"Content": Content,"Plan": Plan,"PostingsLeft": PostingsLeft,"Keywords": Keywords, "TicketID": TicketID,}
    for WhichVariable in WhichVariables:
        number = -1
        for cathegory in CATHEGORIES:
            number += 1
            if cathegory["Cathegory"] == Cathegory:
                CATHEGORIES[number]["Ads"][int(WhichVariable)-1] = Message
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
        print(variable)
        page = results[int(variable) - 1]
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