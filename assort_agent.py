# This is the custome vocode agent that will interact and gather information from the caller

import logging
import os
import redis
import pickle
from typing import Optional, Tuple, AsyncGenerator
import typing
import openai
import json
import os
import asyncio
from vocode.streaming.action.factory import ActionFactory
from vocode.streaming.agent.chat_gpt_agent import ChatGPTAgent
from vocode.streaming.models.agent import AgentConfig, AgentType, CutOffResponse
from vocode.streaming.agent.base_agent import BaseAgent, RespondAgent
from vocode.streaming.agent.factory import AgentFactory
from vocode.streaming.utils.worker import InterruptibleEventFactory
from vocode.streaming.models.message import BaseMessage
from gpt4all import GPT4All

from assortAppointment import assortAppointment, assortState

from dotenv import load_dotenv

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
load_dotenv()

openai.api_key = os.environ.get("OPENAI_API_KEY")


class AssortAgentConfig(AgentConfig, type="agent_assort"):
    cut_off_response: Optional[CutOffResponse] = None


class AssortAgent(RespondAgent[AssortAgentConfig]):
    
    def __init__(self, agent_config: AssortAgentConfig):
        super().__init__(agent_config = agent_config)
        self.redis_conn = redis.Redis(host='localhost', port=6380, decode_responses=False)
    

    async def respond(self, human_input, conversation_id: str, is_interrupt: bool = False) -> Tuple[str, bool]:
        pass

    async def generate_response(self, human_input, conversation_id: str ,is_interrupt: bool = False) -> AsyncGenerator[Tuple[str, bool], None]:
        
        if is_interrupt and self.agent_config.cut_off_response:
            cut_off_response = self.get_cut_off_response()
            yield cut_off_response
            return
        
        # get the assort appointment object if it exits or create it
        if self.redis_conn.exists(conversation_id):
            logger.info(conversation_id)
            assort_appointment = pickle.loads(self.redis_conn.get(conversation_id))
        else:
            logger.info("Creating redis connection")
            assort_appointment = assortAppointment(conversation_id)
            
        admin_message = f"I am sorry I couldn't understand. {assort_appointment.get_current_prompt()}"
        
        #based of of appointment state we will do different things
        match assort_appointment.state:
            case assortState.COMPLAINT:
                if assort_appointment.set_params({'complaint' : human_input}):
                    admin_message = assort_appointment.get_next_prompt()
                    assort_appointment.set_next_state()
                    self.redis_conn.set(conversation_id, pickle.dumps(assort_appointment))
                    yield admin_message
                    return
            case assortState.REFERRAL:
                assort_appointment.set_params({"referral" : human_input})

                admin_message = assort_appointment.get_next_prompt()
                if assort_appointment.referral:
                    assort_appointment.state = assortState.DOCTOR
                else:
                    assort_appointment.state = assortState.APPOINTMENT
                self.redis_conn.set(conversation_id, pickle.dumps(assort_appointment))
                yield admin_message
                return
            case assortState.APPOINTMENT:
                if assort_appointment.set_params({"appointment": human_input}):
                    admin_message = assort_appointment.get_next_prompt()
                    assort_appointment.set_next_state()
                    self.redis_conn.set(conversation_id, pickle.dumps(assort_appointment))
                yield admin_message
                return
            case assortState.DONE:
                yield "Thank you I have already collected all the information I have needed"
                return
        
        #ask openai to parse the date for us
        messages = [ {"role": "system", "content": "You are a intelligent assistant."} ]
        messages.append({"role":"user", "content":f"{assort_appointment.get_extract()}: {human_input}"})
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0613",
            messages=messages,
            temperature= 0
            )
        openai_response = response.choices[0].message.content
        logger.info(openai_response)
        
        # there is an error as try again
        if "it is not possible to create a JSON object with the provided information" in openai_response:
            # openai back off as we might hit the limit
            asyncio.sleep(5)
            yield admin_message
            return
        
        #after we get a response try to parse it and save the values
        try:
            content = json.loads(response.choices[0].message.content.strip())
            if assort_appointment.set_params(content):
                admin_message = assort_appointment.get_next_prompt()
                assort_appointment.set_next_state()
                self.redis_conn.set(conversation_id, pickle.dumps(assort_appointment))
        except Exception as ex:
            logger.error(ex)

        logger.info(f"This is the conversation id: {conversation_id}")
        
        #backoff for openai so we do not hit the limit
        await asyncio.sleep(10)
        yield admin_message
        

#  Agent Factory class to initialize our custom agent
class AssortAgentFactory(AgentFactory):
    def create_agent(self, agent_config: AgentConfig, logger: Optional[logging.Logger]) -> BaseAgent:
        if agent_config.type == "agent_assort":
            return AssortAgent(agent_config=typing.cast(AssortAgentConfig, agent_config))
        raise Exception("Invalid agent config")