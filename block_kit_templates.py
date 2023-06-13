from pprint import pprint

schedule_block_kit = {
    "text": "Your deck is legal!",
    "blocks": [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Your deck is legal!"
            }
        }
    ]
}
# schedule_block_kit = {
#     "text": "Your deck is legal!",
#     "blocks": [
#         {
#             "type": "section",
#             "text": {
#                 "type": "mrkdwn",
#                 "text": "Your deck is legal!"
#             }
#         },
#         {
#             "type": "input",
#             "element": {
#                 "type": "plain_text_input",
#                 "multiline": True,
#                 "initial_value": "My deck this week",
#                 "action_id": "plain_text_input-action"
#             },
#             "label": {
#                 "type": "plain_text",
#                 "text": "Would you like to post it with the following message?",
#                 "emoji": True
#             }
#         },
#         {
#             "type": "actions",
#             "elements": [
#                 {
#                     "type": "button",
#                     "text": {
#                         "type": "plain_text",
#                         "emoji": True,
#                         "text": "Schedule"
#                     },
#                     "style": "primary",
#                     "value": "click_me_123"
#                 },
#                 {
#                     "type": "button",
#                     "text": {
#                         "type": "plain_text",
#                         "emoji": True,
#                         "text": "Cancel"
#                     },
#                     "style": "danger",
#                     "value": "click_me_123"
#                 }
#             ]
#         }
#     ]
# }


def build_schedule_block_kit(message_text):
    schedule_prompt = schedule_block_kit.copy()
    # schedule_prompt["blocks"][1]["element"]["initial_value"] = message_text
    return schedule_prompt


error_block_kit = {
    "text": "Please submit a valid text file!",
    "blocks": [
        {
            "type": "section",
            "text": {
                "type": "plain_text",
                "text": "Please submit a valid text file!",
                "emoji": True
            }
        }
    ]
}


def build_error_block_kit():
    error_prompt = error_block_kit.copy()
    return error_prompt


deck_invalid_block_kit = {
    "text": "Deck invalid",
    "blocks": [
        {
            "type": "section",
            "text": {
                "type": "plain_text",
                "text": "Deck invalid",
                "emoji": True
            }
        }
    ]
}


def build_deck_invalid_block_kit(deck_errors):
    deck_invalid_prompt = error_block_kit.copy()
    deck_invalid_prompt["text"] = "\n".join(deck_errors)
    deck_invalid_prompt["blocks"][0]["text"]["text"] = "\n".join(deck_errors)

    return deck_invalid_prompt
