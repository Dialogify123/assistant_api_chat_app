from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.errors import HttpError
from services.orchestrator import Orchestrator
import time

class GCPOrch(Orchestrator):
    """ GCP Orchestrator class"""
    
    def __init__(self, credentials):
        self.__credentials = credentials
        self.__services = self.validate_get_service()

    def authenticate(self):
        return service_account.Credentials.from_service_account_info(self.__credentials,
                scopes=['https://www.googleapis.com/auth/cloud-platform'])
    
    def get_service(self):
        return build('deploymentmanager', 'v2', credentials = self.authenticate())
    
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
        except HttpError as e:
            return False if e.error_details[0]['reason'] == 'notFound' else True

    def create_vm(self,  template:str, deployment_name:str):
        project = self.__credentials['project_id']
        # if self.vm_exist(project, deployment_name):
        #     return "Already exist"
        # import yaml
        
        # template = yaml.dump(eval(str(yaml.safe_load(template))))
        template = {
        'name': deployment_name,
        'target': {
            'config': {
                'content': template
            }
        }
    }
        request = self.__services.deployments().insert(
            project=project, 
            body=template
            )
        try:
            response = request.execute()
            
            # CONDITION FOR ERROR DURING DEPLOYMENT.
            # if self.check_status(deployment_name):
            #     print("Error occured during this deployment")

        except HttpError as e:
            return e.error_details[0]['message']
        
        if self.staging(project,deployment_name):
            return "Error occur while staging."
        # # error = self.check_status(deployment_name) 
        # if error:
        #     print("Error occured during this deployment")
        #     return error
                # print("Error occured during this deployment")
        return response
        # return f"VM instance created: {response['selfLink']}"
        
    def staging(self, project,deployment_name):
        try:
            instStatus = self.__services.deployments().get(
                project=project,
                deployment = deployment_name
            ).execute()
            # print('staging try: ', instStatus)
            while instStatus['operation']['status'] != 'DONE':
                time.sleep(5)
                instStatus = self.__services.deployments().get(
                    project=project,
                    deployment = deployment_name
                ).execute()
            return False
        except:
            return True

    def validate_credentials(self):
        return all([(key in self.__credentials) for key in [
                        "type",
                        "project_id",
                        "private_key_id",
                        "private_key",
                        "client_email",
                        "client_id",
                        "auth_uri",
                        "token_uri",
                        "auth_provider_x509_cert_url",
                        "client_x509_cert_url",
                        "universe_domain"
                    ]])

    def delete_instance(self, deployment_name):
        project = self.__credentials['project_id']
        if self.vm_exist( project, deployment_name):
            try:
                self.__services.deployments().delete(
                    project=project,
                    deployment = deployment_name
                ).execute()
            except HttpError as e:
                return e.error_details[0]['message']
            return "Delete"
        return "Does not exist"
    
    def check_status(self, deployment_name):
        project = self.__credentials['project_id']
        if self.vm_exist( project, deployment_name):
            try:
                response = self.__services.deployments().get(
                    project=project,
                    deployment = deployment_name
                ).execute()
                
                if response['operation']['error']['errors']:
                    print(response['operation']['error']['errors'])
                    return response['operation']['error']['errors']

            except HttpError as e:
                return e.error_details[0]['message']
            return False
        return False