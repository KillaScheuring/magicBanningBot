from pprint import pprint


class ValidationResponse:
    def __init__(self):
        self.header = "Checking..."
        self.blocks = []

    def get_block_kit(self):
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": self.header,
                    "emoji": True
                }
            },
            {
                "type": "divider"
            }
        ]
        blocks.extend(self.blocks)
        return {
            "text": self.header,
            "blocks": blocks
        }

    def set_file_rejected(self):
        self.header = "File type is incorrect"
        self.blocks = []

    def set_deck_errors(self, errors, warnings):
        self.header = "Deck validation results:"
        self.blocks = []

        if errors:
            self.blocks.extend([{
                "type": "section",
                "text": {
                    "type": "plain_text",
                    "text": ":x: Deck has errors!",
                    "emoji": True
                }
            }])
        else:
            self.blocks.extend([{
                "type": "section",
                "text": {
                    "type": "plain_text",
                    "text": ":white_check_mark: Deck is valid!",
                    "emoji": True
                }
            }])

        # Add error and warning titles
        if errors or warnings:
            titles = []
            if errors:
                titles.append({
                    "type": "mrkdwn",
                    "text": "*Errors*"
                })

            if warnings:
                titles.append({
                    "type": "mrkdwn",
                    "text": "*Warnings*"
                })
            self.blocks.extend([{
                "type": "section",
                "fields": titles
            }])

            # Adjust error and warning lengths to match for fields
            if len(errors) < len(warnings):
                errors += [None] * (len(warnings) - len(errors))
            if len(warnings) < len(errors):
                warnings += [None] * (len(errors) - len(warnings))

            # Add error and warning messages
            self.blocks.extend([{
                "type": "section",
                "fields": [{
                    "type": "plain_text",
                    "text": item,
                    "emoji": True
                } for item in items if item]
            } for items in zip(errors, warnings)])


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
