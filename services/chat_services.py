import json
import openai
import os
from openai import OpenAI
from constants import OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY
os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY

class Assistant:
    
    def __init__(self, instruction, function_definitions, tools):
        self.client = OpenAI()
        self.tool = tools
        self.assistant = self.client.beta.assistants.create(
            name="Dialogify",
            instructions= instruction,
            model="gpt-4-0125-preview",
            tools=function_definitions
        )
        self.threads = {}
    
    def createThread(self, userId):
        thread = self.client.beta.threads.create()
        self.threads[userId] = thread
    
    def deleteThread(self, userId):
        self.threads.pop(userId)
    
    def createMessage(self, userId, prompt = ""):
        return self.client.beta.threads.messages.create(
            thread_id=self.threads[userId].id,
            role="user",
            content=prompt
        )
    
    def runn(self, userId):
        run = self.client.beta.threads.runs.create(
          thread_id=self.threads[userId].id,
          assistant_id=self.assistant.id,
        )
        return run
    
    def checkstatus(self, run, userId):
        while run.status != 'completed':       
            run = self.client.beta.threads.runs.retrieve(
              thread_id=self.threads[userId].id,
              run_id=run.id
            )
            if run.status == 'requires_action':
                # tool_call = run.required_action.submit_tool_outputs.tool_calls[0]
                run = self.client.beta.threads.runs.submit_tool_outputs(
                    thread_id=self.threads[userId].id,
                    run_id=run.id,
                    tool_outputs=[self.performAction(run)],
                )
    
    def performAction(self, run):
            tool_call = run.required_action.submit_tool_outputs.tool_calls[0]
            function = tool_call.function
            function_name = function.name
            arguments = json.loads(function.arguments)
            return { "tool_call_id": tool_call.id, "output": self.tools[function_name](**arguments) }
            
    def runAssistant(self, userId, prompt):
        self.createMessage(userId, prompt)
        run = self.runn(userId)
        self.checkstatus(run, userId)
        messages = self.client.beta.threads.messages.list(
            thread_id=self.threads[userId].id
        )
        return messages.data[0].content[0].text.value