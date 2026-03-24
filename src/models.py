from pydantic import BaseModel

class Intent(BaseModel):
    name: str
    action: str
    notes: str

class Meeting(BaseModel):
    summary: str         # In the future we can make it a sales rep, so we can read the content of fireflies ai and send a follow up 
    start_time: str     
    attendee_name: str
    attendee_email: str

class DraftEmail(BaseModel):
    to: str          # juan@company.com (from calendar attendee)
    subject: str     # "Following up - Next Steps at [Company]"
    body: str        # the full email body    
