from abc import ABC, abstractmethod

class Orchestrator(ABC):
    
    @abstractmethod
    def create_vm(self, credentials:dict, template:dict, deployment_name:str):
        pass