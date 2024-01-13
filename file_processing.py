import docx2txt
from io import BytesIO
import json
import re


def process_ban_list(ban_list_content=None):
    if ban_list_content:
        docx = BytesIO(ban_list_content)

        # Extract text
        text = docx2txt.process(docx)
    else:
        with open("bannedCards.txt", "r") as ban_list_text_file:
            text = ban_list_text_file.read()

    ban_list = {}
    week = "Week 0"
    for row in text.splitlines():
        row = row.replace(":", "").replace("’", "'").strip()
        row = row.replace("ï‚·", "").replace(":", "").replace("â€™", "'").strip()
        if not row or "banned cards" in row.lower():
            continue
        if "Week" in row:
            week = row
            continue
        if len(row.split(". ")) > 1:
            ban_list.setdefault(row.split(". ")[1], week)
        else:
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
        card_name = re.sub("(^[0-9]+)(\s+)", "", row).strip()
        # Flag when at the sideboard
        in_sideboard = in_sideboard or "sideboard" in row.lower()
        # Skip row if no card
        if not card_name or "sideboard" in row.lower():
            continue
        # Retrieve card count
        card_count = int("".join(list(filter(str.isdigit, row))))
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


if __name__ == '__main__':
    process_ban_list()
