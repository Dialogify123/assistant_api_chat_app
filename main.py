import os
from fastapi import FastAPI
from pydantic import BaseModel
from services import chat_services
from trulens_eval import TruBasicApp
from services.vector_db import getTemplate
from services.aws_orchestration import AWSOrch
from services.gcp_orchestration import GCPOrch
from fastapi.middleware.cors import CORSMiddleware
from utils.credentials_mapping import credentials_mapping
from trulens_eval import Feedback, OpenAI as fOpenAI, Tru
from fastapi import WebSocket, WebSocketDisconnect, HTTPException, status
from constants import INSTRUCTION, FUNCTION_GET_TEMPLATE,FUNCTION_DEPLOY_STACK , OPENAI_API_KEY


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




def deployTemplate(region:str = "", provider:str='', deploymentName:str='', template:str=''):
    if provider not in USER_SESSIONS:
        return str({
            "error": f"First create session for {provider}"
        })
    if not USER_SESSIONS[provider][1]:
        USER_SESSIONS[provider][0]['region'] = region
        USER_SESSIONS[provider][1] = AWSOrch(credentials=USER_SESSIONS[provider][0])
    orchestrator = USER_SESSIONS[provider][1]
    print(template)
    return str(orchestrator.create_vm(template, deploymentName))





ASSISTANT = chat_services.Assistant(
    INSTRUCTION, 
    [
        FUNCTION_GET_TEMPLATE,
        FUNCTION_DEPLOY_STACK,
    ], 
    {
        "getTemplate" : getTemplate,
        "deployTemplate" : deployTemplate,
    }
)





fopenai = fOpenAI()
f_answer_relevance = Feedback(fopenai.relevance).on_input_output()
f_context_relavance = Feedback(fopenai.relevance_with_cot_reasons).on_input_output()
tru_llm_standalone_recorder = TruBasicApp(ASSISTANT.runAssistant, app_id="Dialogify123", feedbacks=[f_answer_relevance,f_context_relavance])




app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.post("/session")
async def createSession(credentials: GenericCredentials):
    mappedCerdentials = credentials_mapping(credentials)
    print(mappedCerdentials)
    match credentials.provider:
        case "GCP":
            try:
                USER_SESSIONS["GCP"] = [mappedCerdentials, GCPOrch(credentials=mappedCerdentials)]
            except Exception as e:
                print(e)
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="GCP credentails are not validated")
        case "AWS":
            try:
                USER_SESSIONS["AWS"] = [mappedCerdentials, None]
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