# py-helm-gen
A python package written to allow developers to transform their docker-compose.yaml files into a helm chart. This library will enable users that are unfamiliar with helm and DevOps to handle their own cloud deployments to K8s clusters.  

py-helm-gen will read from an existing docker-compose.yaml file and create it into a starter helm chart all within a few lines of code.  

## How to install  
In your terminal run:  
```
$ pip install pyhelmgen
```

## How to use  
py-helm-gen can be used to productionalize any Python app framework such as Django, FastAPI, or Flask.  

Before using py-helm-gen, make sure you have created a docker-compose.yaml file and have tested running the application with it.  

```
# import the class to migrate your 
from HelmFromComposer import HelmFromComposer

# initialize object of the HelmFromComposer class
compose_file = "docker-compose.yaml"  # path to your docker compose file to this file
app_name = "boaty" 
helm_generator = HelmFromComposer.HelmFromComposer(compose_file, app_name)

# create the helm chart from your object
helm_generator.create_helm_chart()
```

Options for the helm chart can be added at the initialization of the HelmFromComposer object as an argument. These include:  
1. compose_file *(Required):* The path to the docker-compose.yaml file
2. app_name *(Required):* Release name
3. description *(Optional) (Default = A Helm chart for deploying the {{ .Release.Name }} web app)*: Description of the helm chart application  
4. replicas *(Optional) (Default = 1)*:" Number of pod replicas  
5. version *(Optional) (Default = 0.1.0*: Chart version    
6. auto_sync *(Optional) (Default = False)*: Enable true to rebuild your helm chart with every start of the application. Otherwise, HelmFromComposer will check for the helm file and only run when one does not exist.  

## Contact  
If you want to make any contributions to the library please open a pull request on the GitHub repo. If you have any questions please email nick.caravias@gmail.com  
