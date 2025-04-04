from ollama import chat
from ollama import ChatResponse

response:ChatResponse = chat(model="deepseek-r1:14b", messages=[
    {"role": "user", 
     "content": "What is the capital of France?"}
])

print (response.message.content)
