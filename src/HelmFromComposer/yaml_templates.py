'''
yaml_templates.py
file containing methods to get the yaml template for deployment, chart, service, and values.
extracting 
'''

def get_deployment_yaml():
    """
    Function to generate the Kubernetes Deployment YAML template.
    """
    deployment_yaml_content = """apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Release.Name }}-{{ .ServiceName }}
  labels:
    app: {{ .Release.Name }}-{{ .ServiceName }}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: {{ .Release.Name }}-{{ .ServiceName }}
  template:
    metadata:
      labels:
        app: {{ .Release.Name }}-{{ .ServiceName }}
    spec:
      containers:
        - name: {{ .ServiceName }}
          image: "{{ .Values | get (print .ServiceName \".image.repository\") }}:{{ .Values | get (print .ServiceName \".image.tag\") }}"
          ports:
            {{- range .Values[.ServiceName].ports }}
            - containerPort: {{ . }}
            {{- end }}
          env:
            {{- range $key, $value := .Values[.ServiceName].env }}
            - name: {{ $key }}
              value: {{ $value }}
            {{- end }}
"""
    return deployment_yaml_content

def get_service_yaml():
    """
    Function to generate the Kubernetes Service yaml template.
    """
    service_yaml_content = """apiVersion: v1
kind: Service
metadata:
  name: {{ .Release.Name }}-{{ .ServiceName }}
spec:
  selector:
    app: {{ .Release.Name }}-{{ .ServiceName }}
  ports:
    {{- range .Values.{{ .ServiceName }}.ports }}
    - port: {{ . }}
      targetPort: {{ . }}
    {{- end }}
  type: ClusterIP
"""
    return service_yaml_content

def _validate_limits(limits):
  """
  Function to validate limits, ensure that cpu memory and limit end with m and memory ends with 
  Mi or G

  Args:
    limits (dict): dictionary containing the limits for cpu and memory
  """
  if limits['cpu_limit'][-1] != 'm':
    return False
  if limits['memory_limit'][-2:] not in ['Mi', 'Gi']:
    return False
  if limits['cpu_request'][-1] != 'm':
    return False
  if limits['memory_request'][-2:] not in ['Mi', 'Gi']:
    return False
  return True
  
def get_values_yaml(limits):
    """
    Function to generate the values yaml template with placeholders.
    """
    if not _validate_limits(limits):
      values_yaml_content = """webapp:
    image:
      repository: webapp
      tag: latest
    env: {}
    ports: []
    resources:
      limits:
        cpu: 500m
        memory: 512Mi
      requests:
        cpu: 250m
        memory: 256Mi
"""
    else: 
       values_yaml_content = f"""webapp:
    image:
      repository: webapp
      tag: latest
    env: {{}}
    ports: []
    resources:
      limits:
        cpu: {limits['cpu_limit']}
        memory: {limits['memory_limit']}
      requests:
        cpu: {limits['cpu_request']}
        memory: {limits['memory_request']}
"""
       
    return values_yaml_content