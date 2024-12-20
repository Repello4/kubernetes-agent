from flask import Flask,request,jsonify
from util import query_agent,get_cluster_information
import json
from uuid import uuid4
import logging 
from pydantic import BaseModel,ValidationError
import os


# Set the logging level for the root logger to INFO to avoid debug logs from other libraries
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s %(levelname)s - %(message)s',
                    filename='agent.log', filemode='a')

# Set the logging level for your specific logger to DEBUG
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

app = Flask(__name__)


## THis is the conversation history, inplace for multiple user testing
conversation_store = {}

class QueryResponse(BaseModel):
        query: str
        answer: str

conversation_store['1'] = [{
        "role": "system",
        "content": (
            "You are a Kubernetes assistant that responds to queries with concise, "
            "brief answers."
            "Do NOT include extra details, only provide the essential information."
            "Use spaces instead of underscores or commas"
            "Do NOT include identifiers in your response, example: 'mongodb-56c598c8fc' should be 'mongodb' and replace - with spaces"
            "Example Responses:"
            "Q: Which pod is spawned by my-deployment? A: my-pod "
            "Q: What is the status of the pod named 'example-pod'? A: Running "
            "Q: How many nodes are there in the cluster? A: 2 "
            "Q: Which pod is associated with the mongo database? A: mongodb"
            "Dont use A: or Q: in your response thats just for the user and for the assistant just return the answer"
        )
    }]


logger.info("Starting the application...")


@app.route('/start_chat',methods=['POST'])

def start_chat():

    session_id = str(uuid4())

    conversation_store[session_id] = []

    return jsonify({"message": "You are starting a conversation with our AI Agent!", "session_id":session_id})

   




@app.route('/query', methods=['POST'])
def query_agent_api():
    data = request.json
    query = data.get('query')
    logger.debug(f"Received query: {query}")

    session_id = '1'

    if not session_id or session_id not in conversation_store:
        logger.error("Invalid or missing session ID")
        return jsonify({"error": "Invalid or missing session ID."}), 400

    conversation_store[session_id].append({"role": "user", "content": query})

    try:
        response = query_agent(conversation_store[session_id], query)

        validated_response = QueryResponse(query=query, answer=response['message'])
        logger.info(f"User query: {query}")
        logger.info(f"Assistant response: {response['message']}")
        # Append response
        conversation_store[session_id].append({
            "role": "assistant",
            "content": validated_response.answer
        })

        return jsonify(validated_response.model_dump())  

    except Exception as e:
        logger.error(f"Error in /query: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/logs', methods=['GET'])
def get_logs():
    try:
        with open("agent.log", "r") as log_file:
            logs = log_file.read()
        return logs, 200
    except FileNotFoundError:
        return "Log file not found.", 404
    except Exception as e:
        return f"Error reading log file: {str(e)}", 500


@app.route('/get_kube_api',methods = ['GET'])
def get_kube_api():

    try:
        response = get_cluster_information()

        # Validate response using Pydantic
        validated_response = QueryResponse(
            query="Get Kubernetes Cluster Info",
            answer=json.dumps(response) 
        )
        logger.info('Cluster Info: %s',response)
        return jsonify({"cluster_info": validated_response.model_dump()})
    except Exception as e:
        logger.error(f"Error in /get_kube_api: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)