import openai
import requests
from pydantic import BaseModel
from openai import OpenAI
import pdb
import json
import os


API_KEY = os.getenv("OPENAI_API_KEY")

def query_agent(query):

    client = OpenAI(api_key=API_KEY)

    

    class QueryResponse(BaseModel):
        query: str
        answer: str
    
    #openai.pydantic_function_tool(QueryResponse),

    tools = [{
        "type":"function",
        "function":{
            "name": "get_kube",
            "description": "Use this function to get information about the kubernetes cluster",
            "parameters":{
                "type": "object",
                "properties":{

                    "query":{
                        "type": "string",
                        "description": "This is query from the user",
                    
                    }
                },
                "strict":True,
                "required":["query"]
            }
        }
    }
    ]


    #for now will hard code the api key
    #Will be using Open AI function calling, will also define a set of tools the model can use to connect external systems(KUBERNETES)

    messages = [{"role":"user",
                 "content":query}]
    
    response = client.chat.completions.create(
        model= "gpt-4o-mini",
        messages=messages,
        tools=tools,
        tool_choice="auto",
        
    )

    response_message = response.choices[0].message
    messages.append(response_message)




    tool_calls = response_message.tool_calls


    if tool_calls:
        tool_call_id = tool_calls[0].id
        tool_call_function = tool_calls[0].function.name

        if tool_call_function == 'get_kube':

            #pdb.set_trace()


            try:
                response_test = requests.get('http://localhost:5000/get_kube_api')
                if response_test.status_code == 200:

                    
            
                    content = response_test.json()
           
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "name": tool_call_function,
                        "content": content['response']
                    })
                    
                    model_with_kube_info = client.chat.completions.create(
                        model = "gpt-4o-mini",
                        messages=messages,
                    )

                    print(model_with_kube_info.choices[0].message.content)
                    return({"message": model_with_kube_info.choices[0].message.content})
            except Exception as e:
                return(e)
        
        
    
    return {"message": response_message.content}




def get_kube():

    mock_kube_cluster = {
        "name": "FakeCluster",
        "namespace": "example-namespace",
        "nodes": [
            {
                "name": "node1",
                "role": "master",
                "status": "Ready"
            },
            {
                "name": "node2",
                "role": "worker",
                "status": "Ready"
            }
        ],
        "services": [
            {
                "name": "example-service",
                "type": "LoadBalancer",
                "status": "Running"
            }
        ],
        "deployments": [
            {
                "name": "example-deployment",
                "replicas": 3,
                "status": "Running"
            }
        ]
    }
    return json.dumps(mock_kube_cluster)