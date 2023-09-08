#  This class implements an event handler for when the call is cut off.
#  If the call is completed we will send a text message to the number 
#  otherwise we will not do anything and just log some messages


from vocode.streaming.models.events import Event, EventType, PhoneCallEndedEvent
from vocode.streaming.utils import events_manager
import typing
import redis
import pickle
import os
import logging
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()
SID = os.environ.get('TWILIO_ACCOUNT_SID')
TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

from assortAppointment import assortAppointment

class assortEventsManager(events_manager.EventsManager):
    def __init__(self):
        super().__init__(subscriptions=[EventType.PHONE_CALL_ENDED])
        self.redis_conn = redis.Redis(host='localhost', port=6380, decode_responses=False)

    async def handle_event(self, event: Event):
        if event.type == EventType.PHONE_CALL_ENDED:
            phone_call_ended = typing.cast(PhoneCallEndedEvent, event)
            # load the details of the phone call into an object using pickle and redis
            if self.redis_conn.exists(phone_call_ended.conversation_id):
                assort_appointment = pickle.loads(self.redis_conn.get(phone_call_ended.conversation_id))
            else:
                logger.error("an error has occurred")
                return
            if assort_appointment.resolved:
                #create a connection and send a text message to the user
                client = Client(SID, TOKEN)
                message = client.messages.create(
                    from_='18777630132',
                    body=assort_appointment.text_message,
                    to=assort_appointment.phone_number
                    )
            else:
                logger.debug("couldn't complete phone call")