"""Answer a staff question from the help articles (retrieval-augmented generation).

Answers are streamed as events so the Help page can show them as they are written:
    {"type": "delta", "text": "..."}       a piece of the answer, in order
    {"type": "done", "sources": [...]}     the end, with the articles the answer cited
    {"type": "error", "detail": "..."}     the end, when generation failed part-way
"""
import logging
import re

from django.conf import settings
from openai import OpenAIError

from llm.services.client import chat_stream, get_client
from ..prompts import context_message, system_prompt
from .retrieval import retrieve

logger = logging.getLogger(__name__)

NOT_FOUND = ("I couldn't find that in the help docs. Try rephrasing your question, "
             "or ask your branch manager or a super admin.")
STOPPED = "The help assistant stopped before finishing its answer. Please try again."
MAX_TOKENS = 500
TEMPERATURE = 0.1


def _extra_body(model):
    # Qwen3 thinks out loud by default, which is slow and wastes the token budget.
    return {"chat_template_kwargs": {"enable_thinking": False}} if "qwen" in model.lower() else None


def _sources(answer_text, matches):
    """Retrieved articles the answer cited. A refusal cites nothing, so it gets no
    sources, rather than a list of loosely related articles that look like backing."""
    titles = {}
    for match in matches:
        titles.setdefault(match.slug, match.title)
    cited = dict.fromkeys(re.findall(r"\[([a-z0-9-]+)\]", answer_text))
    return [{"slug": slug, "title": titles[slug]} for slug in cited if slug in titles]


def build_messages(role, matches, question, history=()):
    return [
        {"role": "system", "content": system_prompt(role) + "\n\n" + context_message(matches)},
        *({"role": turn["role"], "content": turn["content"]} for turn in history),
        {"role": "user", "content": question},
    ]


def start_answer(user, question, history=()):
    """Find the relevant articles and start the LLM's answer.

    Retrieval and opening the provider stream happen here, so their failures
    raise before any response is sent. Returns an iterator of events.
    """
    matches = retrieve(user.role, question)
    if not matches:
        # Nothing relevant: refuse without calling the LLM, so it cannot make something up.
        return iter([{"type": "delta", "text": NOT_FOUND}, {"type": "done", "sources": []}])
    model = settings.HELP_LLM_MODEL
    pieces = chat_stream(get_client(), build_messages(user.role, matches, question, history), model=model,
                         max_tokens=MAX_TOKENS, temperature=TEMPERATURE, extra_body=_extra_body(model or ""))
    return _events(pieces, matches)


def _events(pieces, matches):
    text = []
    try:
        for piece in pieces:
            text.append(piece)
            yield {"type": "delta", "text": piece}
    except (OpenAIError, ValueError):
        logger.exception("Help chatbot answer failed part-way")
        yield {"type": "error", "detail": STOPPED}
        return
    yield {"type": "done", "sources": _sources("".join(text), matches)}
