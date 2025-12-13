from flask import Flask, request, jsonify
import json
import os
import requests


GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID_LIST = os.getenv("NOTION_DATABASE_ID_LIST")
GIST_ID = os.getenv("GIST_ID")

app = Flask(__name__)
@app.route('/api/data', methods=['GET'])

def main():
    Cathegories, Report_Message_GET_Gist = Get_Cathegories_From_Gist()
    Content, Message_Place, Timespan, TicketID, Plan, Cathegory, Keywords = Get_Content()
    Cathegories_New, Keywords, WhichVariables, Cathegory = handle_data(Cathegories, Content, Plan , Timespan, TicketID, Keywords, Message_Place, Cathegory)
    Report_Message_PATCH_Gist = Update_Cathegories_Gist(Cathegories_New)
    Report_Message_Update_Notion = Update_Notion(Message_Place, Keywords, Cathegory)

    Report = Report_Message_GET_Gist + "\n" + Report_Message_PATCH_Gist + "\n" + "\n".join(Report_Message_Update_Notion)
    print(Report)
    return str(Report), 200


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
    status_codes = []
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
        if response.status_code == 200:
            status_codes.append(f"Page {variable} updated successfully.")
        else:
            status_codes.append(f"Failed to update page {variable}. Status code: {response.status_code}")
    return status_codes

@app.route('/cron', methods=['GET'])
def cron():
    return "Cron job executed", 200

@app.route('/remove', methods=['GET'])
def Start():
    Message_Place_List, Cathegory = Get_Variables()
    CATHEGORIES, Report_Message_Gist_GET = Get_Cathegories_From_Gist()
    CATHEGORIES_New = Remove(Message_Place_List, Cathegory, CATHEGORIES)
    Report_Message_Gist_PATCH = Update_Cathegories_Gist(CATHEGORIES_New)
    status_codes = Update_Notion(Message_Place_List, Keywords="_________", Cathegory=Cathegory)
    Report = Report_Message_Gist_GET + "\n" + Report_Message_Gist_PATCH + "\n" + "\n".join(status_codes)
    return Report,200
def Get_Variables():
    id = "2bd0bcea8f4080e0b98ee41deb945ef3"
    url = f"https://api.notion.com/v1/pages/{id}"
    headers = {
        'Authorization': 'Bearer ' + NOTION_API_KEY,
        'Content-Type': 'application/json',
        'Notion-Version': '2022-06-28',
    }
    response = requests.get(url, headers=headers)
    data = response.json()
    properties = data["properties"]
    Message_Place = properties["Message Place"]["rich_text"][0]["plain_text"]
    Message_Place_List = Message_Place.split(",")
    Cathegory = properties["Cathegory"]["select"]["name"] 
    print(Message_Place_List, Cathegory)
    return Message_Place_List, Cathegory


def Remove(Message_Place_List, Cathegory, CATHEGORIES):
    for Cath in CATHEGORIES:
        if Cath["Cathegory"] == Cathegory:
            for place in Message_Place_List:
                Cath["Ads"][int(place)-1] = {
                    "Content": "",
                    "Plan": "BASE",
                    "PostingsLeft": "",
                    "Keywords": "",
                    "TicketID": "",
                }
    return CATHEGORIES




if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)