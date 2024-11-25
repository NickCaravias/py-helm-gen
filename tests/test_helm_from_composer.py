import os
import sys
import unittest

# Add the 'src' directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from HelmFromComposer import HelmFromComposer

class TestHelmFromComposer:
    def __init__(self) -> None:
        pass
    
    def test_create_helm(self):
        compose_file = "example-docker-compose/fake-app/docker-compose.yaml"  
        app_name = "boaty" 
        helm_generator = HelmFromComposer(compose_file, app_name, description='Helm chart for boaty!', replicas="3", version="3.1.4", app_version="2.0")
        helm_generator.create_helm_chart()
            

if __name__ == "__main__":
    test_object = TestHelmFromComposer()
    test_object.test_create_helm()