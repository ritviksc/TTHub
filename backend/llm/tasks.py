# Register celery tasks for the LLM API endpoint for generating
# responses from the language model
# Make sure tasks use @shared_task decorator to register them with Celery

# We need to run this command so the workers are created
# celery -A config worker -c 4 (create 4 celery workers - change if workload grows)

from celery import shared_task
from .services.client import get_available_models
from django.core import cache
import json

""""
@shared_task
def test_task() -> str:
    print("Celery task executed!")
    return "Done"
"""

"""
For now store them in a cache and fetch them from the LLM
provider API when the system starts up.
At a regular interval, fetch the list of available
models from the LLM provider API and update the list.
This is done using a Celery task that runs at a regular interval
to fetch the list of available models and update the list in memory.
Store the list of available models in a cache (e.g., Redis) to avoid
fetching them from the LLM provider API every time they are needed, or a
database table.

"""
@shared_task
def get_models() -> None:
    """
    Get the list of available LLM models from the LLM provider API.
    Store them in a cache.
    Arguments:
        None    
    Returns:
        None
    """
     
    # Cache the models avaliable
    # Can run this at regular intervals to update models avaliable to users
    if (get_available_models()):
        cache.set("models", json.dumps())
    elif:
        print("Error getting models")
    
    
    
