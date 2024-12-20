import openai
import requests
from pydantic import BaseModel
from openai import OpenAI
import pdb
import json
import os
import pprint
from tenacity import retry, wait_random_exponential, stop_after_attempt
from kubernetes import client,config
from config import get_api_key

API_KEY = get_api_key()
openai_client = OpenAI(api_key=API_KEY)
GPT_MODEL = 'gpt-4o-mini'

#Pydantic Model
class QueryResponse(BaseModel):
        query: str
        answer: str


tools = [{
    "type": "function",
    "function": {
        "name": "get_cluster_information",
        "description": "Use this function to get information about the Kubernetes cluster",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "This is the query from the user"
                },
                "answer": {
                    "type": "string",
                    "description": "The assistant's answer to the query"
                }
            },
            "required": ["query", "answer"]
        }
    }
}]

@retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
def chat_completion_request(messages, tools=None, tool_choice=None, model=GPT_MODEL):
    try:
        response = openai_client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice=tool_choice,
        )
        return response
    
    except Exception as e:
        print("Unable to generate ChatCompletion response")
        print(f"Exception: {e}")
        return e

def query_agent(conversation_history, query):
    try:
        # Request a response from the OpenAI API
        response = chat_completion_request(conversation_history, tools=tools, tool_choice='auto')
        response_message = response.choices[0].message

        # Check for tool calls
        tool_calls = response_message.tool_calls
        if tool_calls:
            conversation_history.append(response_message)
            tool_call_id = tool_calls[0].id
            tool_call_function = tool_calls[0].function.name

            if tool_call_function == 'get_cluster_information':
                try:
                    response_test = requests.get('http://127.0.0.1:8000/get_kube_api')
                    if response_test.status_code == 200:
                        content = response_test.json()
                        
                        # Validate the response with Pydantic
                        validated_tool_output = QueryResponse(
                            query=query,
                            answer=json.dumps(content['cluster_info'])
                        )
                        
                        # Append response to conversation
                        conversation_history.append({
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "name": tool_call_function,
                            "content": validated_tool_output.json()
                        })

                        # Send updated conversation history back to OpenAI
                        model_with_kube_info = chat_completion_request(conversation_history)
                        validated_final_response = QueryResponse(
                            query=query,
                            answer=model_with_kube_info.choices[0].message.content
                        )
                        
                        # Append final assistant response to conversation
                        conversation_history.append({
                            "role": "assistant",
                            "content": validated_final_response.answer
                        })
                        return {"message": validated_final_response.answer}
                except Exception as e:
                    print(f"Error during tool execution: {e}")
                    return {"message": "An error occurred while processing the tool output."}

        # Validate the responses directly
        validated_response = QueryResponse(query=query, answer=response_message.content)
        conversation_history.append({"role": "assistant", "content": validated_response.answer})
        return {"message": validated_response.answer}

    except Exception as e:
        print(f"Error during agent interaction: {e}")
        return {"message": "An error occurred during the agent interaction."}



def get_cluster_information():
    """
    This function fetches information about the Kubernetes cluster.

    Returns:
        str: A JSON string containing information about the cluster.
    """

    node_info = get_node_info()
    service_info = get_service_info()
    pod_info = get_pod_info()
    deployment_info = get_deployments_info()

    cluster_info = {
        "nodes": node_info,
        "pods": pod_info,
        "deployments": deployment_info,
        "services": service_info
    }
    return json.dumps(cluster_info)



def get_node_info():
    """
    This function fetches information about nodes in the Kubernetes cluster.

    Returns:
        list: A list of dictionaries, each containing information about a node.
    """

    config.load_kube_config()
    clust = client.CoreV1Api()

    nodes = clust.list_node()
    node_info = []

    for node in nodes.items:

        node_info.append({
        "name": node.metadata.name,
        "status": node.status.conditions[-1].type,  
        "role": node.metadata.labels.get("kubernetes.io/role", "unknown"),
        })
    return node_info

def get_pod_info(namespace="default"):
    """
    This function fetches information about pods in a given namespace.

    Args:
        namespace (str, optional): The namespace to fetch pod information from. Defaults to "default".

    Returns:
        list: A list of dictionaries, each containing information about a pod.
    """

    config.load_kube_config()
    clust = client.CoreV1Api()

    pods = clust.list_namespaced_pod(namespace=namespace)
    pod_info = []

    for pod in pods.items:

        containers = []

        for container in pod.spec.containers:
            
            containers.append({
                "name": container.name,
                "image": container.image,
                "ports": [{"containerPort": port.container_port, "protocol": port.protocol} for port in (container.ports or [])],
                "env": [{"name": env.name, "value": env.value} for env in (container.env or [])],
                "readinessProbe": container.readiness_probe.http_get.path if container.readiness_probe and container.readiness_probe.http_get else None,
                "livenessProbe": container.liveness_probe.http_get.path if container.liveness_probe and container.liveness_probe.http_get else None,
            })
        #End of container info



        pod_info.append({
            "name": pod.metadata.name,
            "status": pod.status.phase,
            "namespace": pod.metadata.namespace,
            "node_name": pod.spec.node_name,

            #New fields that are possibly in the kube information
            "status": pod.status.phase,
            "volumes": [{"name": vol.name, "type": vol.secret.secret_name if vol.secret else "persistentVolume"} for vol in pod.spec.volumes or []],
            "volumeMounts": [{"name": mount.name, "mountPath": mount.mount_path} for container in pod.spec.containers for mount in container.volume_mounts or []],
            "containers": containers,
        })
    return pod_info

def get_deployments_info(namespace="default"):
    """
    Fetches information about deployments in a given namespace.

    Args:
        namespace (str, optional): The namespace to fetch deployment information from. Defaults to "default".

    Returns:
        list: A list of dictionaries, each containing information about a deployment.
    """
    config.load_kube_config()
    clust = client.AppsV1Api()

    # Fetch deployments
    deployments = clust.list_namespaced_deployment(namespace=namespace)
    deployment_info = []
    for deploy in deployments.items:
        deployment_info.append({
            "name": deploy.metadata.name,
            "replicas": deploy.status.replicas,
            "available_replicas": deploy.status.available_replicas,
            "namespace": deploy.metadata.namespace,
        })
    return deployment_info

def get_service_info(namespace="default"):
    """
    Fetches information about services in a given namespace.

    Args:
        namespace (str, optional): The namespace to fetch service information from. Defaults to "default".

    Returns:
        list: A list of dictionaries, each containing information about a service.
    """
    config.load_kube_config()
    clust = client.CoreV1Api()

    # Fetch services
    services = clust.list_namespaced_service(namespace=namespace)
    service_info = []
    for service in services.items:

        service_ports = []
        for port in service.spec.ports:

            service_ports.append({
                "name": port.name,
                "protocol": port.protocol,
                "port": port.port,
                "target_port": port.target_port,
                "node_port": port.node_port,
                "app_protocol": port.app_protocol
            })

        service_info.append({
            "name": service.metadata.name,
            "type": service.spec.type,
            "cluster_ip": service.spec.cluster_ip,
            "ports": service_ports
        })
    return service_info
