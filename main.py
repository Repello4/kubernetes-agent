from flask import Flask,request,jsonify
from util import query_agent,get_cluster_information
import json
from uuid import uuid4
import logging
from pydantic import BaseModel,ValidationError
import os


logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s %(levelname)s - %(message)s',
                    filename='agent.log', filemode='a')

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
            "Do not include extra details, only provide the essential information."
        )
    }]


logging.info("Starting the application...")


@app.route('/start_chat',methods=['POST'])

def start_chat():

    session_id = str(uuid4())

    conversation_store[session_id] = []

    return jsonify({"message": "You are starting a conversation with our AI Agent!", "session_id":session_id})

   




@app.route('/query', methods=['POST'])
def query_agent_api():
    data = request.json
    query = data.get('query')
    logging.debug(f"Received query: {query}")

    session_id = '1'

    if not session_id or session_id not in conversation_store:
        logging.error("Invalid or missing session ID")
        return jsonify({"error": "Invalid or missing session ID."}), 400

    conversation_store[session_id].append({"role": "user", "content": query})

    try:
        response = query_agent(conversation_store[session_id], query)

        validated_response = QueryResponse(query=query, answer=response['message'])
        logging.info(f"Assistant response: {response['message']}")
        # Append response
        conversation_store[session_id].append({
            "role": "assistant",
            "content": validated_response.answer
        })

        return jsonify({"response": validated_response.model_dump()})  

    except Exception as e:
        logging.error(f"Error in /query: {e}")
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

        return jsonify({"cluster_info": validated_response.model_dump()})
    except Exception as e:
        logging.error(f"Error in /get_kube_api: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)