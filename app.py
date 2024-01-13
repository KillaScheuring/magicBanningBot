import os
from dotenv import load_dotenv
import requests
from slack_bolt import App
import json
from block_kit_templates import ValidationResponse
from file_processing import validate_deck_list, process_ban_list

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
