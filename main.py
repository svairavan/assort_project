#   This is the main entry point for the starts the vocode telephony service


import logging
import os
from fastapi import FastAPI
from vocode.streaming.models.telephony import TwilioConfig
from pyngrok import ngrok
from vocode.streaming.telephony.config_manager.redis_config_manager import (
    RedisConfigManager,
)
from vocode.streaming.models.agent import FillerAudioConfig
from vocode.streaming.models.message import BaseMessage
from vocode.streaming.telephony.server.base import (
    TwilioInboundCallConfig,
    TelephonyServer,
)
from assort_agent import AssortAgentFactory, AssortAgentConfig
from assortEvent import assortEventsManager

from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

config_manager = RedisConfigManager()

BASE_URL = os.getenv("BASE_URL")
if not BASE_URL:
    raise ValueError("BASE_URL environment variable must be set")

AGENT_CONFIG = AssortAgentConfig(
    initial_message=BaseMessage(text="Hi you have reached the Kalevala Medical Group? Can I get your name please?"))

TWILIO_CONFIG = TwilioConfig(
    account_sid=os.getenv("TWILIO_ACCOUNT_SID"),
    auth_token=os.getenv("TWILIO_AUTH_TOKEN"),
    record=True)

INBD_CONFIG = TwilioInboundCallConfig(
    url="/inbound_call",
    agent_config=AGENT_CONFIG,
    twilio_config=TWILIO_CONFIG
)

assort_telephony_server = TelephonyServer(
    base_url=BASE_URL,
    config_manager=config_manager,
    logger=logger,
    inbound_call_configs=[INBD_CONFIG],
    agent_factory=AssortAgentFactory(),
    events_manager=assortEventsManager(),
    
)

app.include_router(assort_telephony_server.get_router())