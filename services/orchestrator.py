from abc import ABC, abstractmethod

class Orchestrator(ABC):
    
    @abstractmethod
    def create_vm(self, template:str, deployment_name:str):
        pass