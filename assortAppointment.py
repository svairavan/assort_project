#  Class for our assort admin information

from datetime import datetime
from enum import Enum
import re

EXTRACT = "Extract data classes ({}) from text and put it in a simple json object"

class assortAppointment:
    def __init__(self, conversation_id: str):
        self.conversation_id = conversation_id # like a uuid created from vocode
        
        #information gathered from the user
        self.first_name: str = None
        self.last_name: str = None
        self.email: str = None
        self.phone_number: str = None
        self.dob: datetime.date = None
        self.medical_complaint: str = None
        self.subsciber_name: str = None
        self.subscriber_id: str = None
        self.address: str = None
        self.referral: bool = False
        self.doctor: str = "Doctor Jacob"
        self.appointment: datetime.date = None
        self.resolved: bool = False
        self.text_message: str = None
        
        # prompts for the user extracts for open ai and how states are related
        self.prompts: dict = {}
        self.extracts: dict = {}
        self.next_state: dict = {}
        
        # will give us the state of the call
        self.state = assortState.NAME
        
        #initialize the assort object.  Populate the extracts prompts and 
        self.initialize()
    
    #Function to intialize the assort object
    def initialize(self):
        # extracts for open ai
        self.extracts = {
            assortState.NAME: EXTRACT.format("firstName, lastName"),
            assortState.DOB: EXTRACT.format("datetime"),
            assortState.PHONE: EXTRACT.format("phone"),
            assortState.EMAIL: EXTRACT.format("email"),
            assortState.SUBSCRIBER: EXTRACT.format("firstName, lastName"),
            assortState.ADDRESS: EXTRACT.format("address"),
            assortState.INSURANCE: EXTRACT.format("insuranceId"),
            assortState.DOCTOR: EXTRACT.format("doctor"),
        }
        #current and next prompts for the user
        self.prompts = {
            assortState.NAME: {
                "current": "Can I get your name please?",
                "next": "What is your date of birth?",
            },
            assortState.DOB: {
                "current": "What is your date of birth?",
                "next": "What is your phone number starting with area code?",
            },
            assortState.PHONE: {
                "current": "What is you phone number starting with area code?",
                "next": "What is your email address?"
            },
            assortState.EMAIL: {
                "current": "What is your email address?",
                "next":  "What is your home address?"
            },
            assortState.ADDRESS:{
                "current": "What is your home address?",
                "next": "What name is listed in your Insurance?"
            },
            assortState.SUBSCRIBER: { 
                "current":  "What name is listed in your Insurance?",
                "next": "What is your insurance id"
            },
            assortState.INSURANCE:{
                "current": "What is your insurance id",
                "next": "what is your reason for coming in?"
            },
            assortState.COMPLAINT: {
                "current": "What is you reason for coming in?",
                "next": "Do you have a referral?"
            },
            assortState.REFERRAL:{
                "current": "Do you have a referral?"
            },
            assortState.DOCTOR: {
                "current": "Which doctor did you get a referral to?",
            },
            assortState.APPOINTMENT: {
                "current": f"I have a Thursday August 31st at 9:00 A.M or Friday September 1st at 12:30 P.M appointment available with {self.doctor}"
            },
            assortState.DONE:{
                "current": "Thank you I have gathered all the information that I need. Goodbye!"
            }
        }
        
        # how states are related.  This has most of the states but can be altered by other functions
        
        self.next_state = {
            assortState.NAME: assortState.DOB,
            assortState.DOB: assortState.PHONE,
            assortState.PHONE: assortState.EMAIL,
            assortState.EMAIL: assortState.ADDRESS,
            assortState.ADDRESS: assortState.SUBSCRIBER,
            assortState.SUBSCRIBER: assortState.INSURANCE,
            assortState.INSURANCE: assortState.COMPLAINT,
            assortState.COMPLAINT: assortState.REFERRAL,
            assortState.DOCTOR: assortState.APPOINTMENT,
            assortState.APPOINTMENT: assortState.DONE
        }
    
    # get current prompt
    def get_current_prompt(self):
        return self.prompts[self.state]["current"]
    
    #get next prompt
    def get_next_prompt(self):
        return self.prompts[self.state]["next"]
    
    #get extract so open ai can parse the information
    def get_extract(self):
        return self.extracts[self.state]
    
    # sets the next state
    def set_next_state(self):
        self.state = self.next_state[self.state]
    
    # after open ai has parsed we will validate and set the assort object parameters dependent on state    
    def set_params(self, content):
        match self.state:
            case assortState.NAME:
                
                if "firstName" not in content or "lastName" not in content or len(content["firstName"]) < 1 or len(content["lastName"]) < 1:
                    return False
                self.first_name = content["firstName"]
                self.last_name = content["lastName"]
                return True
            case assortState.DOB:
                if "date" not in content:
                    return False
                self.date = content["date"]
                return True
            case assortState.PHONE:
                if "phone" not in content or len(content["phone"])!= 10:
                    return False
                self.phone_number = content["phone"]
                return True
            case assortState.EMAIL:
                if "email" not in content:
                    return False
                regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
                if re.fullmatch(regex, content["email"]):
                    self.email = content["email"]
                    return True
                return False
            case assortState.ADDRESS:
                if "address" not in content:
                    return False
                self.address = content["address"]
                return True
            case assortState.SUBSCRIBER:
                if "firstName" not in content or "lastName" not in content or len(content["firstName"]) < 1 or len(content["lastName"]) < 1:
                    return False
                self.subsciber_name = f"{content['firstName']}  {content['lastName']}"
                return True
            case assortState.INSURANCE:
                if "insuranceId" not in content:
                    return False
                self.subscriber_id = content["insuranceId"]
                return True
            case assortState.COMPLAINT:
                if "complaint" not in content:
                    return False
                self.medical_complaint = content["complaint"]
                return True
            case assortState.REFERRAL:
                if "yes" in content["referral"].lower():
                    self.referral = True
                    self.prompts[assortState.REFERRAL]["next"] = "Which doctor did you get a referral to?"
                else:
                    self.prompts[assortState.REFERRAL]["next"] = f"I have a Thursday August 31st or Friday September 1st appointment available with {self.doctor}.  Which appointment would you like?"
                return True
            case assortState.DOCTOR:
                if "name" not in content:
                    return False
                self.doctor = content["name"]
                self.prompts[assortState.DOCTOR]["next"] = f"I have a Thursday August 31st or Friday September 1st appointment available with {self.doctor}.  Which appointment would you like?"
                return True
            case assortState.APPOINTMENT:
                text = content["appointment"].lower()
                if any([x in text for x in ["friday", "sepetember"]]):
                    self.appointment = datetime(2023, 9, 1, 12, 30)
                elif any([x in text for x in ["thursday", "august"]]):
                    self.appointment = datetime(2023, 8, 31, 9,0)
                else:
                    return False
                month = self.appointment.strftime("%B")
                day = self.appointment.strftime("%-d")
                year = self.appointment.strftime("%Y")
                day_name = self.appointment.strftime("%A")
                hour = self.appointment.strftime("%-I")
                minute = self.appointment.strftime("%M")
                ampm = self.appointment.strftime("%p")
                prompt_text = f"We have scheduled an appointment for you on {day_name} {month} {day} {year} at {hour}:{minute} {ampm} with {self.doctor}.  Thank you Goodbye!"
                self.prompts[assortState.APPOINTMENT]["next"] = prompt_text
                self.prompts[assortState.DONE]["current"] = prompt_text
                self.text_message = prompt_text
                self.resolved = True
                return True
            case assortState.DONE:
                self.resolved = True
                return True
            case _:
                return False

#Enum for states
class assortState(Enum):
    NAME = 1
    DOB = 2
    PHONE = 3
    EMAIL = 4
    COMPLAINT = 5
    ADDRESS = 6
    SUBSCRIBER = 7
    INSURANCE = 8
    REFERRAL = 9
    DOCTOR = 10
    APPOINTMENT = 11
    DONE = 12