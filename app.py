import os
from dotenv import load_dotenv
import requests
from slack_bolt import App
import json
import re
from pprint import pprint
from block_kit_templates import build_schedule_block_kit, build_error_block_kit, build_deck_invalid_block_kit

load_dotenv()
SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')
SLACK_BOT_USER_TOKEN = os.getenv('SLACK_BOT_USER_TOKEN')
SLACK_SIGNING_SECRET = os.getenv('SLACK_SIGNING_SECRET')

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
        return True, file_request.text
    if file_type == "docx":
        return None, None
    return None, None


def validate_deck_list(deck_text):
    """

    :param str deck_text:
    :return: bool
    """
    with open("bannedCards.json", "r") as ban_list_file:
        banned_cards = json.load(ban_list_file)
    errors = []
    for row in deck_text.splitlines():
        row = re.sub("(^[0-9])(\s+)", "", row).strip()
        if not row or "sideboard" in row.lower():
            continue
        if row in banned_cards:
            errors.append(f"{row} was banned {banned_cards[row]}")

    return errors


def deck_response(channel_id, message_text, slack_file_dict):
    if "sideboard" in message_text.lower():
        file_status, file_text = True, message_text.split("```")[1]
        message_text = message_text.split("```")[0]
    else:
        file_status, file_text = handle_file_attachment(slack_file_dict)

    if file_status is None:
        app.client.chat_postMessage(channel=channel_id, **build_error_block_kit())
        return

    if file_status:
        deck_errors = validate_deck_list(file_text)
        if deck_errors:
            app.client.chat_postMessage(channel=channel_id, **build_deck_invalid_block_kit(deck_errors))
            return
        else:
            app.client.chat_postMessage(channel=channel_id, **build_schedule_block_kit(message_text))
            return


@app.event("file_created")
def read_file_created(client, event, logger):
    # Todo make this check for new ban list
    print("File created!")
    print("event")
    print(event)
    files = app.client.files_list()
    print("files")
    pprint(files.get("files"))
    file_info = app.client.files_info(file=event["file_id"])
    print("file info")
    pprint(file_info)


@app.message()
def read_dm(message):
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
                            "text": "*Welcome to your _App's Home_* :tada:"
                        }
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "This button won't do much for now but you can set up a listener for it using the `actions()` method and passing its unique `action_id`. See an example in the `examples` folder within your Bolt app."
                        }
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "Click me!"
                                }
                            }
                        ]
                    }
                ]
            }
        )

    except Exception as e:
        logger.error(f"Error publishing home tab: {e}")


# Start your app
if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 3000)))
