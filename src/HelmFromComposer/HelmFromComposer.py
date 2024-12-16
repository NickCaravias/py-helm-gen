import os
import yaml
import logging
from .yaml_templates import get_deployment_yaml, get_service_yaml, get_values_yaml

class HelmFromComposer:
    def __init__(self, compose_file: str, 
                 app_name: str, 
                 description: str = "A Helm chart for deploying the {{ .Release.Name }} web app", 
                 replicas: str = "1",
                 version: str = "0.1.0",
                 app_version: str = "1.0",
                 auto_sync: bool = False):
        self.compose_file = compose_file
        self.app_name = app_name
        self.description = description  
        self.replicas = replicas
        self.version = version
        self.app_version = app_version
        self.chart_name = f"{self.app_name}-chart"
        self.chart_dir = f"./{self.chart_name}"
        self.templates_dir = os.path.join(self.chart_dir, "templates")
        self.values_data = {}  # contains data for the resulting values file

        # Check if the helm chart already exists and if it does not make a directory for it
        if not os.path.exists(self.chart_dir) or auto_sync:
            os.makedirs(self.chart_dir)

    def create_helm_chart(self):
        '''
        Create the Helm chart structure:
        <app_name>-chart
        |--- Chart.yaml
        |--- values.yaml
        |--- templates/
        |------ deployment-<app_name>.yaml
        |------ service-<app_name>.yaml

        This function is used to read the docker-compose file, and first calls the helper methods 
        create_values_yaml and create_values_yaml to create the file structure and templates, 
        then calls _add_values_for_service, _generate_deployment, and generate_service to
        populate the helm chart files. RHCH.
        '''

        # Create chart.yaml 
        self.create_chart_yaml()

        # Use the provided compose_file path directly
        self.compose_file = os.path.abspath(self.compose_file)

        # Create sub directory for helm templates if it does not exist yet
        if not os.path.exists(self.templates_dir):
            os.makedirs(self.templates_dir)

        # Read docker-compose.yaml
        try:
            with open(self.compose_file, 'r') as f:
                compose_data = yaml.safe_load(f)
        except Exception as e:
            print(e.errno)
            print("ERROR: Error opening docker-compose.yaml. Please check your docker-compose path and contents.")
            raise Exception("ERROR: Error opening docker-compose.yaml. Please check your docker-compose path and contents.")
        
        # Iterate through services and generate templates
        for service_name, service_data in compose_data['services'].items():
            # Skip DB services, these are primarily cloud services that are not defined in a helm chart
            if 'db' not in service_name.lower():
                self._add_values_for_service(service_name, service_data)
                self._generate_deployment(service_name, service_data)
                self.generate_service(service_name, service_data)
        self.create_values_yaml()

    def create_chart_yaml(self):
        '''
        Function to add a template for the Chart.yaml file. There is no data needed from
        the docker-compose.yaml so all 
        '''
        chart_yaml_content = f"""apiVersion: v2
name: {self.chart_name}
description: {self.description}
version: {self.version}
appVersion: {self.app_version}
"""
        
        with open(os.path.join(self.chart_dir, 'Chart.yaml'), 'w') as f:
            f.write(chart_yaml_content)

    def create_values_yaml(self):
        '''
        Initialize values.yaml with dynamic placeholders 
        '''
        values_yaml_path = os.path.join(self.chart_dir, 'values.yaml')
        with open(values_yaml_path, 'w') as f:
            # Get the initial content from get_values_yaml
            initial_content = yaml.safe_load(get_values_yaml())
            
            # Merge initial content with values_data
            merged_content = initial_content.copy()
            for key, value in self.values_data.items():
                if key in merged_content:
                    merged_content[key].update(value)
                else:
                    merged_content[key] = value

            # Add a basic structure to the YAML
            merged_content.update({
                "imagePullSecrets": [],
                "replicaCount": int(self.replicas),  # Ensure replicaCount is an integer
                "serviceAccount": {
                    "create": False,
                    "name": ""
                }
            })
            
            try:
                # Dump the merged content into the values.yaml file
                yaml.dump(merged_content, f, default_flow_style=False, allow_unicode=True)
            except Exception as e:
                print(e.errno)
                print("ERROR: OS error writing values yaml file.")
                raise Exception("ERROR: OS error writing values yaml file.")

    def generate_service(self, service_name, service_data):
        '''
        Generate Kubernetes service yaml from the service yaml in templates

        @param: service_name : str : name of the application that the service yaml is defining
        @param: service_data : dict : contents of the yaml template for a helm service file
        '''

        service_template = get_service_yaml()
        service_content = service_template.replace("{{ .ServiceName }}", service_name)

        # Replace placeholders for ports
        if 'ports' in service_data:
            ports = "\n".join([f"    - port: {port.split(':')[0]}\n      targetPort: {port.split(':')[0]}" for port in service_data['ports']])
            service_content = service_content.replace("{{- range .Values.{{ .ServiceName }}.ports }}\n    - port: {{ . }}\n      targetPort: {{ . }}\n    {{- end }}", ports)
        else:
            service_content = service_content.replace("{{- range .Values.{{ .ServiceName }}.ports }}\n    - port: {{ . }}\n      targetPort: {{ . }}\n    {{- end }}", "")

        try:
            with open(os.path.join(self.templates_dir, f"service-{service_name}.yaml"), 'w') as f:
                f.write(service_content)
        except Exception as e:
            print(e.errno)
            print("ERROR: OS error saving service yaml file")
            raise Exception("ERROR: OS error saving service yaml file")

    def _generate_deployment(self, service_name, service_data):
        '''
        Generate Kubernetes Deployment yaml with the contents of the docker-compose.yaml, including
        data such as env variables, image repository, image tag, ports. Eventually writes updates to 
        the apps deployment yaml file.
        
        @param: service_name : str : name of the application that the deployment yaml is defining
        @param: service_data : dict : contents of the yaml template for a helm deployment file
        '''
        
        deployment_template = get_deployment_yaml()
        deployment_content = deployment_template.replace("{{ .ServiceName }}", service_name)

        # Replace placeholders for image, ports, and environment variables
        deployment_content = deployment_content.replace(
            "{{ .Values[.ServiceName].image.repository }}", service_data['image'])
        deployment_content = deployment_content.replace(
            "{{ .Values[.ServiceName].image.tag }}", "latest")

        # Add environment variables
        if 'environment' in service_data:
            if isinstance(service_data['environment'], dict):
                env_vars = "\n".join([
                    f"            - name: {env_key}\n              value: {env_value}"
                    for env_key, env_value in service_data['environment'].items()
                ])
            elif isinstance(service_data['environment'], list):
                env_vars = "\n".join([
                    f"            - name: {item.split('=')[0]}\n              value: {item.split('=')[1]}"
                    for item in service_data['environment']
                ])
            else:
                env_vars = ""
            deployment_content = deployment_content.replace("{{ .Values[.ServiceName].env }}", env_vars)
        else:
            deployment_content = deployment_content.replace("{{ .Values[.ServiceName].env }}", "")

        # Add ports from docker-compose.yaml
        if 'ports' in service_data:
            ports = "\n".join([f"            - containerPort: {port.split(':')[0]}" for port in service_data['ports']])
            deployment_content = deployment_content.replace("{{ .Values[.ServiceName].ports }}", ports)
        else:
            deployment_content = deployment_content.replace("{{ .Values[.ServiceName].ports }}", "")

        try:
            with open(os.path.join(self.templates_dir, f"deployment-{service_name}.yaml"), 'w') as f:
                f.write(deployment_content)
        except Exception as e:
            print(e.errno)
            print("ERROR: OS error writing deployment yaml file")
            raise Exception("ERROR: OS error writing deployment yaml file")

    def _add_values_for_service(self, service_name, service_data):
        '''
        Add values from docker-compose.yaml to values.yaml, data includes image, environment variables, and ports
        
        @param: service_name : str : name of the application that the service yaml is defining
        @param: service_data : dict : contents of the yaml template for a helm service file
        '''
        service_values = {}

        # Add image repository and tag
        if 'image' in service_data:
            image_data = service_data['image'].split(':') if ':' in service_data['image'] else [service_data['image'], 'latest']
            service_values['image'] = {
                'repository': image_data[0],
                'tag': image_data[1]
            }

        # Add environment variables
        if 'environment' in service_data:
            if isinstance(service_data['environment'], dict):
                service_values['env'] = {key: value for key, value in service_data['environment'].items()}
            elif isinstance(service_data['environment'], list):
                service_values['env'] = {item.split('=')[0]: item.split('=')[1] for item in service_data['environment']}
            else:
                service_values['env'] = {}

        # Add container ports
        if 'ports' in service_data:
            service_values['ports'] = [port.split(':')[0] for port in service_data['ports']]

        # Update the values_data dictionary for this service
        self.values_data[service_name] = service_values