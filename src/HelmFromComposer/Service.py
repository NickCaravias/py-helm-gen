from .yaml_templates import get_deployment_yaml, get_service_yaml, get_values_yaml
import os

class Service:
    def __init__(self, 
                 file_path: str,
                 name: str = "{{ .Release.Name }}",
                 version: str = "{{ .Values.appVersion }}", 
                 url: str = "{{ .Values.url }}",
                 ports: list = [8080]):
        self.file_path = file_path
        self.name = name
        self.version = version
        self.url = url

    def create_service(self):
        self.generate_service()


    def generate_service(self):
        '''
        Generate Kubernetes service yaml from the service yaml in templates

        @param: service_name : str : name of the application that the service yaml is defining
        @param: service_data : dict : contents of the yaml template for a helm service file
        '''

        service_template = get_service_yaml()
        service_content = service_template.replace("{{ .ServiceName }}", service_name)

        # Replace placeholders for ports
        if self.ports:
            ports = "\n".join([f"    - port: {ports.split(':')[0]}\n      targetPort: {ports.split(':')[0]}" for port in self.ports])
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