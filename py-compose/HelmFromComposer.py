import os
import shutil
import yaml

class HelmFromComposer:
    def __init__(self, compose_file: str, app_name: str, description: str = "A Helm chart for deploying the {{ .Release.Name }} web app", replicas: str = "1"):
        self.compose_file = compose_file
        self.app_name = app_name
        self.desciption = description
        self.replicas = replicas
        self.chart_name = f"{self.app_name}-chart"
        self.chart_dir = f"./{self.chart_name}"
        self.templates_dir = os.path.join(self.chart_dir, "templates")
        self.values_data = {} # contains data for the resulting values file

        # check if the helm chart already exists and if it does not make a directory for it
        if not os.path.exists(self.chart_dir):
            os.makedirs(self.chart_dir)

        self.create_helm_chart()

    def create_helm_chart(self):
        """
        Create the Helm chart structure:
        <app_name>-chart
        |--- Chart.yaml
        |--- values.yaml
        |--- templates/
        |------ deployment-<app_name>.yaml
        |------ service-<app_name>.yaml

        This function is used to read the docker-compose file, and first calls the helper methods 
        create_values_yaml and create_values_yaml to create the file structure and templates, 
        then calls add_values_for_service, generate_deployment, and generate_service to
        populate the helm chart files. 
        """

        # Create chart.yaml 
        self.create_chart_yaml()

        # Create sub directory for helm templates if it does not exist yet
        if not os.path.exists(self.templates_dir):
            os.makedirs(self.templates_dir)

        # Read docker-compose.yaml and convert services
        with open(self.compose_file, 'r') as f:
            compose_data = yaml.safe_load(f)

        print("DEBUG: Compose Data", compose_data)  # Debug print to check the data

        # Iterate through services and generate templates
        for service_name, service_data in compose_data['services'].items():
            print(f"DEBUG: Processing service {service_name}")  # Debug print
            if 'db' not in service_name.lower():  # Skip DB services
                self.generate_service(service_name, service_data)
                self.generate_deployment(service_name, service_data)
                self.add_values_for_service(service_name, service_data)
                self.create_values_yaml()

        # Debugging: Check if values_data is being populated
        print("DEBUG: values_data before writing to values.yaml", self.values_data)

    def create_chart_yaml(self):
        """Create chart.yaml."""
        chart_yaml_content = f"""
apiVersion: v2
name: {self.chart_name}
description: A Helm chart for Kubernetes deployment
version: 0.1.0
"""
        with open(os.path.join(self.chart_dir, 'Chart.yaml'), 'w') as f:
            f.write(chart_yaml_content)

    def create_values_yaml(self):
        """Create values.yaml with dynamic placeholders."""
        with open(os.path.join(self.chart_dir, 'values.yaml'), 'w') as f:
            # Make sure we add a basic structure to the YAML
            f.write("imagePullSecrets: []\n")
            f.write(f"replicaCount: {self.replicas}\n")
            f.write("serviceAccount:\n")
            f.write("  create: false\n")
            f.write("  name: \"\"\n")
            
            # Dump the values_data for the services into the values.yaml file
            yaml.dump(self.values_data, f, default_flow_style=False, allow_unicode=True)


    def generate_service(self, service_name, service_data):
        """Generate Kubernetes service YAML."""
        service_template = self.read_template('service-template.yaml')
        service_content = service_template.replace("{{ .ServiceName }}", service_name)
        
        with open(os.path.join(self.templates_dir, f"service-{service_name}.yaml"), 'w') as f:
            f.write(service_content)

    def generate_deployment(self, service_name, service_data):
        """Generate Kubernetes Deployment YAML."""
        deployment_template = self.read_template('deployment-template.yaml')
        deployment_content = deployment_template.replace("{{ .ServiceName }}", service_name)

        # Replace dynamic placeholders for image, ports, and environment variables
        deployment_content = deployment_content.replace(
            "{{ .Values[.ServiceName].image.repository }}", service_data['image'])
        deployment_content = deployment_content.replace(
            "{{ .Values[.ServiceName].image.tag }}", "latest")

        # Handle environment variables
        if 'environment' in service_data:
            env_vars = "\n".join([
                f"            - name: {env_key}\n              value: {env_value}"
                for env_key, env_value in service_data['environment'].items()
            ])
            deployment_content = deployment_content.replace("{{ .Values[.ServiceName].env }}", env_vars)
        else:
            deployment_content = deployment_content.replace("{{ .Values[.ServiceName].env }}", "")

        # Handle ports dynamically
        if 'ports' in service_data:
            ports = "\n".join([f"            - containerPort: {port.split(':')[0]}" for port in service_data['ports']])
            deployment_content = deployment_content.replace("{{ .Values[.ServiceName].ports }}", ports)
        else:
            deployment_content = deployment_content.replace("{{ .Values[.ServiceName].ports }}", "")

        with open(os.path.join(self.templates_dir, f"deployment-{service_name}.yaml"), 'w') as f:
            f.write(deployment_content)

    def add_values_for_service(self, service_name, service_data):
        """Add dynamic values for image, environment variables, and ports to values.yaml."""
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
            service_values['env'] = {key: value for key, value in service_data['environment'].items()}

        # Add ports
        if 'ports' in service_data:
            service_values['ports'] = [port.split(':')[0] for port in service_data['ports']]  # Just container ports

        # add replica count from this class's argument
        # service_values['replicaCount'] = self.replicas

        # Update the values_data dictionary for this service
        self.values_data[service_name] = service_values

        # Debugging: Check the values added for the service
        print(f"DEBUG: values_data for service {service_name}", self.values_data[service_name])

    def read_template(self, template_name):
        """Read a raw Helm template file."""
        template_path = os.path.join(os.path.dirname(__file__), 'templates', template_name)
        with open(template_path, 'r') as template_file:
            return template_file.read()


# Usage Example
if __name__ == "__main__":
    # Specify path to the Docker Compose file and the app name
    compose_file = "example-docker-compose/fake-app/docker-compose.yaml"  
    app_name = "boaty" 
    helm_generator = HelmFromComposer(compose_file, app_name, description='Helm chart for boaty!', replicas="3")
