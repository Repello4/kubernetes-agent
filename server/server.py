from flask import Flask,request,jsonify
from util import query_agent,get_kube
import json

app = Flask(__name__)


@app.route('/query',methods= ['POST'])
def query_agent_api():

    query = request.json.get('query')

    try:
        response = query_agent(query)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    return jsonify({'response':response['message']})


@app.route('/get_kube_api',methods = ['GET'])
def get_kube_api():

    response = get_kube()
    
    
    return jsonify({'response': response})


if __name__ == "__main__":
    app.run(debug=True)