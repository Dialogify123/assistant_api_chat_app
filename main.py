from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi import WebSocket, WebSocketDisconnect, HTTPException, status
from constants import INSTRUCTION, FUNCTION_GET_TEMPLATE,FUNCTION_DEPLOY_STACK , OPENAI_API_KEY
from services import chat_services
from services.vector_db import getTemplate
from pydantic import BaseModel
from services.aws_orchestration import AWSOrch
from services.gcp_orchestration import GCPOrch
from utils.credentials_mapping import credentials_mapping
import os
from trulens_eval import Feedback, OpenAI as fOpenAI, Tru
from trulens_eval import TruBasicApp
from trulens_eval.app import App
# from trulens_eval.feedback.provider.openai import OpenAI as f2OpenAI
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

tru = Tru()
tru.reset_database()

class GenericCredentials(BaseModel):
    provider : str
    type : str
    project_id: str
    private_key_id: str
    private_key: str 
    client_email: str
    client_id: str
    auth_uri: str
    token_uri: str
    auth_provider_url: str
    client_url: str
    universe_domain: str


app = FastAPI()
USER_SESSIONS = {}



def deployTemplate(provider:str='', deploymentName:str='', template:str=''):
    print(provider, deploymentName, template)
    print(USER_SESSIONS)
    if provider not in USER_SESSIONS:
        return str({
            "error": f"First create session for {provider}"
        })
    orchestrator = USER_SESSIONS[provider]
    return str(orchestrator.create_vm(template, deploymentName))

tools = {
    "getTemplate" : getTemplate,
    "deployTemplate" : deployTemplate,
}
function_definitions = [
    FUNCTION_GET_TEMPLATE,
    FUNCTION_DEPLOY_STACK
    ]

ASSISTANT = chat_services.Assistant(INSTRUCTION, function_definitions, tools)
fopenai = fOpenAI()
f_answer_relevance = Feedback(fopenai.relevance).on_input_output()
f_context_relavance = Feedback(fopenai.relevance_with_cot_reasons).on_input_output()
tru_llm_standalone_recorder = TruBasicApp(ASSISTANT.runAssistant, app_id="Dialogify123", feedbacks=[f_answer_relevance,f_context_relavance])

origins = [
    '*'
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.post("/session")
async def createSession(credentials: GenericCredentials):
    mappedCerdentials = credentials_mapping(credentials)
    match credentials.provider:
        case "GCP":
            try:
                USER_SESSIONS["GCP"] = GCPOrch(credentials=mappedCerdentials)
            except Exception as e:
                print(e)
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="GCP credentails are not validated")
        case "AWS":
            try:
                USER_SESSIONS["AWS"] = AWSOrch(credentials=mappedCerdentials)
            except:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="AWS credentails are not validated")
    return {
        'response': "Session is created"
    }

@app.websocket("/message")
async def websocket_endpoint(websocket: WebSocket):
    try:
        await websocket.accept()
        ASSISTANT.createThread()
        try:
            while True:
                data = await websocket.receive_text()
                with tru_llm_standalone_recorder as recording:
                    system_response = tru_llm_standalone_recorder.app(data)
                await websocket.send_text(system_response)
        except WebSocketDisconnect:
            ASSISTANT.deleteThread()
    except:
        pass

tru.run_dashboard()