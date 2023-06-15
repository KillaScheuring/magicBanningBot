import os
from dotenv import load_dotenv
import requests
from slack_bolt import App
import slack_sdk
import json
import re
import docx2txt
from io import BytesIO

from pprint import pprint
from block_kit_templates import ValidationResponse

# slack_sdk.web.slack_response.SlackResponse.get()

load_dotenv()
SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')
SLACK_BOT_USER_TOKEN = os.getenv('SLACK_BOT_USER_TOKEN')
SLACK_SIGNING_SECRET = os.getenv('SLACK_SIGNING_SECRET')
BANNED_CARDS_CHANNEL = os.getenv('BANNED_CARDS_CHANNEL')

encoder = json.JSONEncoder()

# Initializes your app with your bot token and signing secret
app = App(
    token=SLACK_BOT_TOKEN,
    signing_secret=SLACK_SIGNING_SECRET
)


# app = AsyncApp(
#     token=SLACK_BOT_TOKEN,
#     signing_secret=SLACK_SIGNING_SECRET
# )


def handle_file_attachment(slack_file_dict):
    if not slack_file_dict:
        return None, None

    file_url = slack_file_dict.get("url_private_download")
    if not file_url:
        return None, None

    # Request the file from slack
    file_request = requests.get(file_url, stream=True, headers={'Authorization': 'Bearer ' + SLACK_BOT_USER_TOKEN})

    file_type = file_url.split(".")[-1]
    if file_type == "txt":
        return "txt", file_request.text
    if file_type == "docx":
        print("Docx!")
        return "docx", file_request.content
    return None, None


def process_ban_list(ban_list_content):
    docx = BytesIO(ban_list_content)

    # Extract text
    text = docx2txt.process(docx)

    ban_list = {}
    week = "Week 0"
    for row in text.splitlines():
        row = row.replace(":", "").replace("’", "'").strip()
        if not row or "banned cards" in row.lower():
            continue
        if "Week" in row:
            week = row
            continue
        ban_list.setdefault(row, week)
    with open("bannedCards.json", "w") as ban_list_json_file:
        json.dump(ban_list, ban_list_json_file)


def validate_deck_list(deck_text):
    """

    :param str deck_text:
    :return: bool
    """
    with open("bannedCards.json", "r") as ban_list_file, open("card_exceptions.json", "r") as card_exceptions_file:
        banned_cards = json.load(ban_list_file)
        card_exceptions = json.load(card_exceptions_file)
    errors, warnings = [], []
    card_count_mainboard = 0
    card_count_sideboard = 0
    in_sideboard = False
    for row in deck_text.splitlines():
        card_name = re.sub("(^[0-9])(\s+)", "", row).strip()
        # Flag when at the sideboard
        in_sideboard = in_sideboard or "sideboard" in row.lower()
        # Skip row if no card
        if not card_name or "sideboard" in row.lower():
            continue
        # Retrieve card count
        card_count = int(list(filter(str.isdigit, row))[0])
        # Check number of card
        # Cards that are not exempt from the play set rule
        not_exempt = card_name not in card_exceptions["playset"] and card_count > 4
        # Cards that have a larger play set
        limited_exempt = card_name in card_exceptions["playset"] and 0 < card_exceptions["playset"][card_name] < card_count
        if not_exempt or limited_exempt:
            errors.append(("count", f"Too many ({card_count}) copies of {card_name}"))

        # Add number of card to totals
        if in_sideboard:
            card_count_sideboard += card_count
        else:
            card_count_mainboard += card_count

        # Check if card is banned
        if card_name in banned_cards:
            errors.append(("ban", f"{card_name} was banned {banned_cards[card_name]}"))

    if card_count_sideboard != 15:
        message = f"Too %s ({card_count_sideboard}) cards in sideboard"
        if card_count_sideboard > 15:
            errors.append(("count", message % "many"))
        else:
            warnings.append(message % "few")

    if card_count_mainboard != 60:
        message = f"Too %s ({card_count_mainboard}) cards in mainboard"
        if card_count_mainboard < 60:
            errors.append(("count", message % "few"))
        else:
            warnings.append(message % "many")

    errors.sort()
    return [error for error_type, error in errors], warnings


def deck_response(channel_id, message_text, slack_file_dict):
    if "sideboard" in message_text.lower():
        file_status, file_text = True, message_text.split("```")[1]
        message_text = message_text.split("```")[0]
    else:
        file_status, file_text = handle_file_attachment(slack_file_dict)

    response_block = ValidationResponse()
    response = app.client.chat_postMessage(channel=channel_id, text="Checking...")

    if file_status is None:
        response_block.set_file_rejected()
        app.client.chat_postMessage(channel=channel_id, **response_block.get_block_kit())
        return

    deck_errors, deck_warnings = validate_deck_list(file_text)
    response_block.set_deck_errors(deck_errors, deck_warnings)
    app.client.chat_update(channel=channel_id, ts=response.get("ts"), **response_block.get_block_kit())


@app.event("file_shared")
def read_file_created(client, event, logger):
    if event.get("channel_id") != BANNED_CARDS_CHANNEL:
        return
    print("file_shared")
    file_info = client.files_info(file=event["file_id"])
    file_status, file_content = handle_file_attachment(file_info.get("file"))
    if type(file_content) == str:
        return
    process_ban_list(file_content)


@app.message()
def read_dm(message):
    print("read_dm")
    message_files_list = message.get("files", [])
    if not message_files_list and "sideboard" not in message.get("text").lower():
        return
    deck_response(message.get("channel"), message.get("text"), message_files_list[0] if message_files_list else None)


@app.event("message")
def handle_message_events(body, logger, event):
    """

    :param dict body:
    :param logger:
    :param dict event:
    :return:
    """
    print("handle_message_events")
    message_files_list = body.get("event", {}).get("files", [])
    if not message_files_list:
        return
    deck_response(event.get("channel"), "", message_files_list[0])


# Add functionality here
@app.event("app_home_opened")
def update_home_tab(client, event, logger):
    try:
        # views.publish is the method that your app uses to push a view to the Home tab
        client.views_publish(
            # the user that opened your app's app home
            user_id=event["user"],
            # the view object that appears in the app home
            view={
                "type": "home",
                "callback_id": "home_view",

                # body of the view
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*Welcome to Magic Banning Bot* :tada:"
                        }
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "To check a deck, go to the messages tab above and either upload a txt or "
                                    "paste a deck inside a codeblock. I will check the deck and let you know "
                                    "if it has any banned cards!"
                        }
                    }
                ]
            }
        )

    except Exception as e:
        logger.error(f"Error publishing home tab: {e}")


# Start your app
if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 3000)))
