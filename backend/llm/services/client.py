# Communicate with LLM provider API to generate responses from the language model
"""
    Tool use notes:
      * Tool calling is enabled with --enable-auto-tool-choice
      * The model-specific parser is set with --tool-call-parser
      * Qwen 3.6 and Qwen 3.5 use qwen3_coder
      * Gemma 4 uses gemma4 plus the Gemma 4 tool chat
        template
      * Output token limits should be controlled per request
        using the client/API max_tokens setting, rather than
        hard-coded globally in the vLLM launch command

"""

from django.conf import settings
from openai import OpenAI

client = OpenAI(api_key=settings.OPENAI_API_KEY, base_url=settings.LLM_API_ENDPOINT)  

def generate(prompt: str, model: str = settings.DEFAULT_LLM_MODEL, max_tokens: int = 100, temperature: float = 0.2) -> str:
    """
    Generate a response from the LLM provider API based on the provided messages.
    
    Arguments:
        prompt (str): The input prompt for the LLM. Will be created using data in the database.

        model (str): The model to use for generating the response.
        Default is set to the DEFAULT_LLM_MODEL from settings.py.

        max_tokens (int): The maximum number of tokens to generate in the response.
        Default is set to 100 tokens. Change as required based on lenght/processing time of the response.

        temperature (float): Sampling temperature for randomness in the response.
        Default is set to 0.2. The range of sampling temperatures is between 0 and 2. Higher values like 0.8 will make the output more random, 
        while lower values like 0.2 will make it more focused and deterministic.
        Change as required based on the desired randomness of the response.
        
    Returns:
        str: The generated response content from the LLM.
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {'role': 'system', 'content': 'You are a helpful and concise AI assistant that will summarise data and generate a report like a professional.'},
                {'role': 'user', 'content': prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating response: {e}")
        return None

def get_available_models() -> list:
    """
    Get the list of available LLM models from the LLM provider API.

    Arguments:
        None
    
    Returns:
        list: A list of available LLM models.
    """
    try:
        models = client.models.list()
        return [model.id for model in models.data]
    except Exception as e:
        print(f"Error fetching available models: {e}")
        return []