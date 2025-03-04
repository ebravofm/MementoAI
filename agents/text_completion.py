
from utils.logger import logger

import requests
import json

from config import DI_TOKEN, MODEL_ID_DI, BASE_URL_DI


def text_completion(prompt: str,
                    # model: ChatOpenAI,
                    max_tokens: int = 1024,
                    temperature: float = 0.7,
                    stop: str = '\n',
                    frequency_penalty: float = 1.1,
                    base_url: str = BASE_URL_DI,
                    model_name: str = MODEL_ID_DI,
                    api_key: str = DI_TOKEN):
    
    
    base_url = f"{base_url}/completions"   
     
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    data = {
        'model': model_name, 
        'prompt': prompt,            
        'max_tokens': max_tokens,   
        'temperature': temperature,
        'frequency_penalty': frequency_penalty,
        'stop': stop
    }

    response = requests.post(base_url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        response_dict = response.json()
        text = response_dict['choices'][0]['text'].strip()
        
        return text
    
    else:
        response.raise_for_status()
        

