import os
import sys
import unittest
import shutil
import yaml

# Add the 'src' directory to the Python path in order to import HelmFromComposer
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from HelmFromComposer.HelmFromComposer import HelmFromComposer

class TestHelmFromComposer(unittest.TestCase):
    def setUp(self):
        self.compose_file = os.path.abspath(os.path.join(os.path.dirname(__file__), 'example-docker-compose/react-node-redis-pg/docker-compose.yaml'))
        self.app_name = "boaty"
        self.helm_generator = HelmFromComposer(self.compose_file, self.app_name, description='Helm chart for boaty!', replicas="3", version="3.1.4", app_version="2.0")
        self.chart_dir = self.helm_generator.chart_dir
        self.templates_dir = os.path.join(self.chart_dir, "templates")

        # Ensure the templates directory exists
        os.makedirs(self.templates_dir, exist_ok=True)

    def test_create_chart_yaml(self):
        self.helm_generator.create_chart_yaml()
        chart_yaml_path = os.path.join(self.chart_dir, 'Chart.yaml')
        self.assertTrue(os.path.exists(chart_yaml_path))

        with open(chart_yaml_path, 'r') as f:
            content = f.read()
            self.assertIn('apiVersion: v2', content)
            self.assertIn(f'name: {self.helm_generator.chart_name}', content)
            self.assertIn(f'description: {self.helm_generator.description}', content)
            self.assertIn(f'version: {self.helm_generator.version}', content)
            self.assertIn(f'appVersion: {self.helm_generator.app_version}', content)

    def test_create_values_yaml(self):
        self.helm_generator.create_values_yaml()
        values_yaml_path = os.path.join(self.chart_dir, 'values.yaml')
        self.assertTrue(os.path.exists(values_yaml_path))

        with open(values_yaml_path, 'r') as f:
            content = f.read()
            self.assertIn('imagePullSecrets: []', content)
            self.assertIn(f'replicaCount: {self.helm_generator.replicas}', content)

    def test_generate_service(self):
        service_name = 'web'
        service_data = {
            'image': 'nginx:latest',
            'ports': ['80:80'],
            'environment': {
                'ENV_VAR': 'value'
            }
        }
        self.helm_generator.generate_service(service_name, service_data)
        service_yaml_path = os.path.join(self.chart_dir, 'templates', f'service-{service_name}.yaml')
        self.assertTrue(os.path.exists(service_yaml_path))

    def test_generate_deployment(self):
        service_name = 'web'
        service_data = {
            'image': 'nginx:latest',
            'ports': ['80:80'],
            'environment': {
                'ENV_VAR': 'value'
            }
        }
        self.helm_generator._generate_deployment(service_name, service_data)
        deployment_yaml_path = os.path.join(self.chart_dir, 'templates', f'deployment-{service_name}.yaml')
        self.assertTrue(os.path.exists(deployment_yaml_path))

    def test_add_values_for_service(self):
        service_name = 'web'
        service_data = {
            'image': 'nginx:latest',
            'ports': ['80:80'],
            'environment': {
                'ENV_VAR': 'value'
            }
        }
        self.helm_generator._add_values_for_service(service_name, service_data)
        self.assertIn(service_name, self.helm_generator.values_data)
        self.assertEqual(self.helm_generator.values_data[service_name]['image']['repository'], 'nginx')
        self.assertEqual(self.helm_generator.values_data[service_name]['image']['tag'], 'latest')
        self.assertEqual(self.helm_generator.values_data[service_name]['env']['ENV_VAR'], 'value')
        self.assertEqual(self.helm_generator.values_data[service_name]['ports'], ['80'])

    def test_create_helm_chart(self):
        self.helm_generator.create_helm_chart()
        values_yaml_path = os.path.join(self.chart_dir, 'values.yaml')
        self.assertTrue(os.path.exists(values_yaml_path))
        with open(values_yaml_path, 'r') as f:
            content = f.read()
        self.assertTrue(os.path.exists(os.path.join(self.chart_dir, 'Chart.yaml')))

if __name__ == "__main__":
    unittest.main()