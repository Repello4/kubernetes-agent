# Kubernetes Agent
This project implements a Flask-based Kubernetes assistant that interacts with a Kubernetes cluster and responds to user queries. It uses OpenAI's GPT model with tools to provide concise, JSON-formatted responses to Kubernetes-related questions.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Prerequisites](#prerequisites)
- [Steps to Installation](#steps-to-installation)
- [Endpoints](#endpoints)
- [Checklist](#check-before-you-start)
- [License](#license)


## Features

**Kubernetes-Agent** is an AI powered assistant that will analyze your kubernetes cluster and answer all of the specifics regarding it.

The Agent:
- Handles user queries and provides accurate answers in JSON format
- Retrieves Kubernetes cluster information which includes nodes, pods, deployments and services
- Utilizes OpenAI's Function Callinf for intuitive query handling

By using the power of function calling the LLM can and will determine when to fetch you information about your deployed cluster. All you need to locate is your kubeconfig file its fair game!

## Installation

### Prerequisites
- Python 3.10 and above.
- Kubernetes cluster is properly configured and running (ensure the location of config file)
- Retrieve OpenAI Key
- Flask is installed

### Steps to Installation

#### 1. Clone the repository


   ```bash
   git clone <repository-url>
   cd <repository-folder>
   ```

#### 2. Create a vitual environment and install dependencies

    ```bash
    conda create --name <env_name>
    conda activate <env_name>
    pip install -r requirements.txt
    ```

#### 3. Set OpenAI API key

    ```bash
    API_KEY = your_api_key
    ```

#### 4. Configure the Kubernetes cluster (minikube and kubectl)
- Start minikube

    ```bash
    minikube start
    ```
- Make sure kubectl is working
    ```bash
    kubectl get nodes
    ```

## Running the Application

### Start the Backend
Run the Flask application

```bash
python main.py
```

- Note that the application will run on http://0.0.0.0:8000

## Endpoints

### 1. /query
- **Methods** : POST
- **Description**: Sends a query to the Agent and receives a response

### Example

```bash
curl -X POST http://localhost:8000/query \
-H "Content-Type: application/json" \
-d '{"query":"Which pod is spawned by my-deployment?"}'
```
- **Response**

```bash
{
  "response": {
    "query": "Which pod is spawned by my-deployment?",
    "answer": "my-pod"
  }
}
```

### 2. /start_chat

- **Methods** : POST
- **Description**: Starts a chat with the Agent, ensuring a unique identifier `session_id`. For each user currently the session_id is hard coded to 1.

### Example

```bash
curl -X POST http://localhost:8000/start_chat '
```
- **Response**

```bash
{
  "response": {
    "message": "You are starting a conversation with our AI Agent!", 
    "session_id": hkljsdj23sd12
    }
}
```

### 3. /get_kube_api
- **Methods** : POST
- **Description**: Fetches detailed information about the Kubernetes cluster. (This is mainly used internally by the Agent)

### Example

```bash
curl -X GET http://localhost:8000/get_kube_api'
```
- **Response**

```bash
{
  "cluster_info": {
    "query": "Get Kubernetes Cluster Info",
    "answer": "{...}"  // JSON representation of cluster details
  }
}
```

## Check before You Start!

 - [ ] Start Backend: Ensure the backend runs on http://0.0.0.0:8000.
 - [ ] Endpoints Tested: Confirm /start_chat, /query, and /get_kube_api work as expected.
 - [ ] Log Debugging: Logs are written to agent.log.
 - [ ] Concise Responses: Ensure responses follow the format:

```json
{
  "query": "Which pod is spawned by my-deployment?",
  "answer": "my-pod"
}
```
**Have Fun!**

## License 

This project is licensed under the MIT License

