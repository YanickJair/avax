import os
import re
import pickle
import base64

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


class GmailListener:
    """This class is responsible for reading incoming emails in our inbox.
    It exposes a webHook URL that is configured in Gmail API/
    """
    TOKEN_FILE = "token.pickle"
    SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
    EMAIL_FROM_PATTERN = r'(?:([^<]*?)\s*<)?([^>]+)>?'

    def __init__(self):
        self.creds = None
        self.service = None
        self.watch_callback_url = "webhook_url"

    
    def authenticate(self):
        if os.path.exists(self.TOKEN_FILE):
            with open(self.TOKEN_FILE, "rb") as token:
                self.creds = pickle.load(token)

        if not self.creds or not self.creds.value:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials.json", self.SCOPES
                )
                self.creds = flow.run_local_server(port=0)
            
            with open(self.TOKEN_FILE, "wb") as token:
                pickle.dump(self.creds, token)

        self.service = build("gmail", "v1", credentials=self.creds)

    async def email_watch(self) -> bool:
        """This function will push email to feed agent"""
        try:
            request = {
                "labelIds": ["INBOX"],
                "topicName": "projects/your-project/topics/your-topic",
                "labelFilterAction": "include"
            }
            if self.service:
                self.service.users().watch(userId="me", body=request).execute()
                return True
        except Exception as exc:
            ...
        return False
            
    async def process_email(self, message_id: str):
        try:
            if self.service:
                message = self.service.users().messages().get(
                    userId="me",
                    id=message_id,
                    format="full"
                ).execute()

                headers = message["payload"]["headers"]
                subject = next(h["value"] for h in headers if h["name"] == "Subject")
                sender = next(h["value"] for h in headers if h["name"] == "From")

                if "parts" in message["payload"]:
                    body = self._get_body_from_parts(message["payload"]["parts"])
                else:
                    body = base64.urlsafe_b64decode(
                        message["payload"]["body"]["data"]
                    ).decode("utf-8")

                    # TODO: Call agent to create ticket

                    # Mark email as checked to avoid duplication
                    self.service.users().messages().modify(
                        userId="me",
                        id=message_id,
                        body={"removeLabelIds": ["UNREAD"]}
                    ).execute()
        except Exception as exc:
            pass

    def _get_body_from_parts(self, parts):
        pass

    def parse_email_sender(self, from_header: str) -> dict:
        """Parser function that gets email and name from 'From' header.

        Example:
        - Jane Doe <jane@doe.com> -> {'name': 'Jane Doe', 'email': 'jane@doe.com'}
        - 'jane Doe' -> {'name': None, 'email': 'jane@doe.com'}
        """
        name = None
        email = None
        if match := re.match(self.EMAIL_FROM_PATTERN, from_header):
            name = match.group(1).strip() if match.group(1) else None
            email = match.group(2).strip()

        return {"name": name, "email": email or from_header}