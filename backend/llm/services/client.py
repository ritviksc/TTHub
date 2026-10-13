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
from django.core.exceptions import ImproperlyConfigured
from openai import OpenAI

_client = None


def get_client():
    """
    Create client on the first use, then reuse it for
    subsequent requests (lazy initialisation)
    """
    global _client

    if _client is None:
        if not settings.LLM_API_ENDPOINT:
            raise ImproperlyConfigured("LLM_API_ENDPOINT must be configured.")

        if not settings.OPENAI_API_KEY:
            raise ImproperlyConfigured("OPENAI_API_KEY must be configured.")
        _client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.LLM_API_ENDPOINT,
            timeout=200.0,
            max_retries=0
        )

    return _client   


def generate(client: OpenAI, prompt: str, sys_prompt: str, model: str | None = None, max_tokens: int = 100, temperature: float = 0.2) -> str:
    """
    Generate a response from the LLM provider API based on the provided messages.
    Arguments:
        client (OpenAI): Pass client that will generate request
        prompt (str): The input prompt for the LLM. Will be created using data in the database.

        model (str): The model to use for generating the response.
        Default is set to the DEFAULT_LLM_MODEL from settings.py.
        sys_prompt (str) : The fixed instructions for the LLM to operate on.

        max_tokens (int): The maximum number of tokens to generate in the response.
        Default is set to 100 tokens. Change as required based on length/processing time of the response.

        temperature (float): Sampling temperature for randomness in the response.
        Default is set to 0.2. The range of sampling temperatures is between 0 and 2.
        Higher values like 0.8 will make the output more random,
        while lower values like 0.2 will make it more focused and deterministic.
        Change as required based on the desired randomness of the response.
    Returns:
        str: The generated response content from the LLM.
    """

    return chat(
        client,
        [
            {'role': 'system', 'content': sys_prompt},
            {'role': 'user', 'content': prompt}
        ],
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
    )


def chat(client: OpenAI, messages: list[dict], model: str | None = None, max_tokens: int = 100, temperature: float = 0.2, extra_body: dict | None = None) -> str:
    """
    Send a full message list (system rules, earlier turns and the new question)
    and return the reply text. generate() is the single-prompt form of this call.
    Arguments:
        messages (list[dict]): Chat messages, each {'role': ..., 'content': ...}.
        extra_body (dict | None): Provider-specific options, e.g. turning Qwen3
        thinking off with {"chat_template_kwargs": {"enable_thinking": False}}.
        Other arguments are as for generate().
    Returns:
        str: The generated response content from the LLM.
    """

    if model is None:
        model = settings.DEFAULT_LLM_MODEL

    if not model or not model.strip():
        raise ImproperlyConfigured(
            "Pass a model or configure DEFAULT_LLM_MODEL."
        )

    # Only send extra_body when asked, so existing calls stay byte-for-byte the same.
    options = {'extra_body': extra_body} if extra_body else {}
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
        **options
    )

    if not response.choices:
        raise ValueError("LLM returned no response choices.")

    choice = response.choices[0]

    if choice.finish_reason == "length":
        raise ValueError("LLM response reached the token limit.")

    if choice.finish_reason != "stop":
        raise ValueError(
            f"LLM response did not finish normally: {choice.finish_reason}"
        )
        
    message_content = choice.message.content

    if message_content is None or not message_content.strip():
        raise ValueError("LLM returned no usable text.")

    return message_content


def chat_stream(client: OpenAI, messages: list[dict], model: str | None = None, max_tokens: int = 100, temperature: float = 0.2, extra_body: dict | None = None):
    """
    Streaming form of chat(): returns an iterator of text pieces as the model
    writes them. The request is sent before this returns, so connection and
    configuration errors raise here, before anything has been shown to a user.
    Arguments: as for chat().
    Returns:
        Iterator[str]: Text pieces. Iterating raises ValueError at the end if the
        reply was cut off by max_tokens or did not finish normally.
    """

    if model is None:
        model = settings.DEFAULT_LLM_MODEL

    if not model or not model.strip():
        raise ImproperlyConfigured(
            "Pass a model or configure DEFAULT_LLM_MODEL."
        )

    options = {'extra_body': extra_body} if extra_body else {}
    stream = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
        stream=True,
        **options
    )
    return _stream_text(stream)


def _stream_text(stream):
    finish_reason = None
    try:
        for chunk in stream:
            # Some providers send a final usage-only chunk with no choices.
            if not chunk.choices:
                continue
            choice = chunk.choices[0]
            if choice.delta is not None and choice.delta.content:
                yield choice.delta.content
            if choice.finish_reason:
                finish_reason = choice.finish_reason
    finally:
        # Stops generation upstream too when the reader goes away mid-answer.
        close = getattr(stream, "close", None)
        if close:
            close()

    if finish_reason == "length":
        raise ValueError("LLM response reached the token limit.")

    if finish_reason != "stop":
        raise ValueError(
            f"LLM response did not finish normally: {finish_reason}"
        )
    

def get_available_models() -> list:
    """
    Get the list of available LLM models from the LLM provider API.
    Arguments:
        None   
    Returns:
        list: A list of available LLM models.
    """
    client = get_client()
    models = client.models.list(timeout=4.0)
    return [model.id for model in models.data]
