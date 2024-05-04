import time
import boto3
from json import loads
from services.orchestrator import Orchestrator

class AWSOrch(Orchestrator):
    """ AWS Orchestrator class"""

    def __init__(self, credentials):
        self.__credentials = credentials
        self.__services = self.validate_get_service()


    def authenticate(self):
        return boto3.Session(
                    region_name=self.__credentials["region"],
                    aws_access_key_id=self.__credentials["access_key"],
                    aws_secret_access_key=self.__credentials["secret_access_key"]
            )
    
    def get_service(self):
        return self.authenticate().client('cloudformation')
    
    def validate_get_service(self):
        if not self.validate_credentials():
            return
        return self.get_service()

    def vm_exist(self, project,  deployment_name):
        try:
            self.__services.deployments().get(
                    project=project,
                    deployment = deployment_name
                ).execute()
            return True
        except:
            return False 

    def create_vm(self, template:str, deployment_name:str):
        # template = str(loads(template))
        # print(template)
        try:
            response = self.__services.create_stack(
                StackName=deployment_name,
                TemplateBody=template,
            )
        except Exception as e:
            return {"error":str(e.args[0])}
        
        if self.staging(deployment_name, 'CREATE_COMPLETE'):
            events = self.describe_events(deployment_name)['StackEvents']
            print(events)
            self.__services.delete_stack(StackName=deployment_name)
            return {    
                        "error":"Error occur while staging",
                        "details": [event for event in events if event['ResourceStatus'] == "CREATE_FAILED" or event['ResourceStatus'] == "ROLLBACK_IN_PROGRESS" or event['ResourceStatus'] == "ROLLBACK_COMPLETE"]
                    }
        return response
        
    def staging(self, deployment_name, status):
        try:
            response = self.__services.describe_stacks(StackName=deployment_name)
            while response['Stacks'][0]['StackStatus'] != status:
                if response['Stacks'][0]['StackStatus'] in  ['ROLLBACK_IN_PROGRESS', 'ROLLBACK_COMPLETE']:
                    return True
                time.sleep(5)
                response = self.__services.describe_stacks(StackName=deployment_name)
            return False
        except:
            return True

    def validate_credentials(self):
        return all([(key in self.__credentials) for key in [
                        "access_key",
                        "secret_access_key",
                        "region"
                    ]])

    def describe_events(self, deployment_name:str):
        return self.__services.describe_stack_events(
            StackName = deployment_name
        )

    def delete_instance(self, deployment_name):
        try:
            response = self.__services.delete_stack(
                StackName=deployment_name,
            )
        except Exception as e:
            return {"error":str(e.args[0])}
        


