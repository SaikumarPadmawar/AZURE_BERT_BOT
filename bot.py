# bot.py
from botbuilder.core import ActivityHandler, TurnContext, MessageFactory
from botbuilder.schema import ChannelAccount, Attachment
from chroma import query_collection  # Import the query function from chroma.py

class CustomQABot(ActivityHandler):
    def __init__(self):
        super().__init__()

    async def on_message_activity(self, turn_context: TurnContext):
        user_input = turn_context.activity.text

        if len(user_input) == 1:
            await turn_context.send_activity("Please provide a meaningful input")
            return

        # Process user input using ChromaDB
        answer, suggestions = query_collection(user_input)

        if not answer:
            await self.select_product(turn_context)
            return

        attachment_content = self.create_card(answer, suggestions)
        attachment = Attachment(content_type="application/vnd.microsoft.card.adaptive", content=attachment_content)
        await turn_context.send_activity(MessageFactory.attachment(attachment))

    async def select_product(self, turn_context: TurnContext):
        # Send an adaptive card for product selection
        card_content = {
            "type": "AdaptiveCard",
            "body": [
                {
                    "type": "TextBlock",
                    "size": "Medium",
                    "weight": "Bolder",
                    "text": "Please select a product:"
                }
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "Camera",
                    "data": "Camera"
                },
                {
                    "type": "Action.Submit",
                    "title": "Smoke",
                    "data": "Smoke"
                }
            ],
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "version": "1.3"
        }
        attachment = Attachment(content_type="application/vnd.microsoft.card.adaptive", content=card_content)
        await turn_context.send_activity(MessageFactory.attachment(attachment))

    def create_card(self, answer, suggestions):
        # Replace newline characters with HTML line break tags
        answer = answer.replace('\n', '<br>')

        # Generate buttons for suggestions
        buttons = []
        for suggestion in suggestions:
            buttons.append({
                "type": "Action.Submit",
                "title": suggestion,
                "data": suggestion
            })

        # Create card content with answer and suggestion buttons
        card_content = {
            "type": "AdaptiveCard",
            "body": [
                {
                    "type": "TextBlock",
                    "size": "Medium",
                    "weight": "Bolder",
                    "text": "Answer"
                },
                {
                    "type": "TextBlock",
                    "text": answer,
                    "wrap": True
                },
                {
                    "type": "TextBlock",
                    "size": "Medium",
                    "weight": "Bolder",
                    "text": "Suggestions"
                }
            ],
            "actions": buttons,
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "version": "1.3"
        }

        return card_content

    async def on_members_added_activity(self, members_added: ChannelAccount, turn_context: TurnContext):
        for member_added in members_added:
            if member_added.id != turn_context.activity.recipient.id:
                await turn_context.send_activity("Hello and welcome!")
