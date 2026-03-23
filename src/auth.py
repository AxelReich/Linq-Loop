import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    'https://www.googleapis.com/auth/calendar.readonly', # To read the meetings
    'https://www.googleapis.com/auth/gmail.modify'       # To read and draft emails
]

def authenticate_google():
    """
    Handles the OAuth 2.0 flow for Google APIs.
    Returns valid credentials to be used by Calendar and Gmail services.
    """
    creds = None
    
    # The token.json file stores your user's access and refresh tokens.
    # It is created automatically after you log in for the first time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
    # If there are no valid credentials available, prompt the user to log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # If the token is just expired but we have a refresh token, silently refresh it.
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            
        # Save the fresh credentials so we don't have to log in again next time.
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
            
    return creds

if __name__ == '__main__':
    # This block allows you to test the auth flow directly by running: python src/auth.py
    print("Starting authentication flow...")
    credentials = authenticate_google()
    print("Authentication successful! You are ready to use the APIs.")