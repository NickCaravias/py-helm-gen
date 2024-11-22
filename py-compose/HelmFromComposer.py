import os
import shutil
import yaml

class HelmFromComposer:
    def __init__(self, compose_file: str, app_name: str):
        self.compose_file = compose_file
        self.app_name = app_name
        self.chart_name = f"{self.app_name}-chart"
        self.chart_dir = f"./{self.chart_name}"
        self.templates_dir = os.path.join(self.chart_dir, "templates")

        if not os.path.exists(self.chart_dir):
            os.makedirs(self.chart_dir)

        self.create_helm_chart()

    def create_helm_chart(self):
        """Create the Helm chart structure."""
        # Create chart.yaml and values.yaml
        self.create_chart_yaml()
        self.create_values_yaml()

        # Create templates directory
        if not os.path.exists(self.templates_dir):
            os.makedirs(self.templates_dir)

        # Read docker-compose.yaml and convert services
        with open(self.compose_file, 'r') as f:
            compose_data = yaml.safe_load(f)

        # Iterate through services and generate templates
        for service_name, service_data in compose_data['services'].items():
            if 'db' not in service_name.lower():  # Skip DB services
                self.generate_service(service_name, service_data)
                self.generate_deployment(service_name, service_data)

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
        values_content = f"""
imagePullSecrets: []
replicaCount: 1
serviceAccount:
  create: false
  name: ""
"""
        with open(os.path.join(self.chart_dir, 'values.yaml'), 'w') as f:
            f.write(values_content)

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
            ports = "\n".join([f"            - containerPort: {port}" for port in service_data['ports']])
            deployment_content = deployment_content.replace("{{ .Values[.ServiceName].ports }}", ports)
        else:
            deployment_content = deployment_content.replace("{{ .Values[.ServiceName].ports }}", "")

        with open(os.path.join(self.templates_dir, f"deployment-{service_name}.yaml"), 'w') as f:
            f.write(deployment_content)

    def read_template(self, template_name):
        """Read a raw Helm template file."""
        template_path = os.path.join(os.path.dirname(__file__), 'templates', template_name)
        with open(template_path, 'r') as template_file:
            return template_file.read()


# Usage Example
if __name__ == "__main__":
    # Specify path to the Docker Compose file and the app name
    compose_file = "example-docker-compose/fake-app/docker-compose.yaml"  # Adjust to your path
    app_name = "fakeapp"  # Set your desired app name
    helm_generator = HelmFromComposer(compose_file, app_name)
