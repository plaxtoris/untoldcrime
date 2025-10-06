"""LLM interface for story generation."""

from typing import Optional
from prompts import prompt_builder
from config import LITELLM_MASTER_KEY, DOMAIN_WRAPPER, API_TIMEOUT
import requests
import logging
import json

logger = logging.getLogger(__name__)


class LLMError(Exception):
    """Base exception for LLM-related errors."""
    pass


class LLMConnectionError(LLMError):
    """Raised when connection to LLM API fails."""
    pass


class LLMResponseError(LLMError):
    """Raised when LLM response cannot be parsed."""
    pass


def generate_story(
    model: str = "zalazium-fast",
    word_limit: int = 200,
    setting: str = "Bitcoin Darknet"
) -> Optional[dict[str, str]]:
    """Generate a crime story using LLM.

    Args:
        model: LLM model to use
        word_limit: Target word count for the story
        setting: Story setting/theme

    Returns:
        Dictionary with 'story', 'title', and 'summary' keys, or None on failure
    """
    response_format = {
        "story": "Hier kommt der Text der Geschichte hin.",
        "title": "Erzeuge ein Titel für die Geschichte mit maximal 5 Wörten",
        "summary": "Hier kommt die Kurzfassung der Geschichte in etwa 45 Wörtern hin",
    }
    prompt_sys = prompt_builder(word_limit=word_limit, setting=setting)
    return _call_llm(
        model=model,
        prompt_sys=prompt_sys,
        prompt_usr=None,
        response_format=response_format
    )


def _call_llm(
    model: str,
    prompt_sys: str,
    prompt_usr: Optional[str] = None,
    response_format: Optional[dict[str, str]] = None
) -> Optional[dict[str, str]]:
    """Make an LLM API call.

    Args:
        model: LLM model identifier
        prompt_sys: System prompt
        prompt_usr: Optional user prompt
        response_format: Expected response structure

    Returns:
        Parsed response or None on failure
    """
    try:
        url = f"https://{DOMAIN_WRAPPER}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {LITELLM_MASTER_KEY}",
            "Content-Type": "application/json"
        }

        messages = [{"role": "system", "content": prompt_sys}]
        if prompt_usr:
            messages.append({"role": "user", "content": prompt_usr})

        data = {"model": model, "messages": messages}
        if response_format:
            data["response_format"] = _build_response_format(response_format)

        response = requests.post(url, headers=headers, json=data, timeout=API_TIMEOUT)
        response.raise_for_status()

        return _parse_response(response, response_format or {})

    except requests.RequestException as e:
        logger.error(f"LLM API request failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in LLM call: {e}")
        return None


def _build_response_format(response_format: dict[str, str]) -> dict:
    """Build JSON schema for structured output.

    Args:
        response_format: Dictionary mapping field names to descriptions

    Returns:
        JSON schema dictionary
    """
    properties = {
        key: {"description": value}
        for key, value in response_format.items()
    }

    return {
        "type": "json_schema",
        "json_schema": {
            "name": "response_schema",
            "schema": {
                "type": "object",
                "properties": properties,
                "required": list(response_format.keys()),
                "additionalProperties": False
            }
        }
    }


def _parse_response(
    response: requests.Response,
    response_format: dict[str, str]
) -> dict[str, str]:
    """Parse and validate LLM response.

    Args:
        response: HTTP response from LLM API
        response_format: Expected response structure

    Returns:
        Parsed data or fallback dictionary
    """
    fallback = {key: "no_data" for key in response_format}

    try:
        content = response.json()["choices"][0]["message"]["content"].strip("` \n")

        # Remove markdown code block markers
        if content.lower().startswith("json"):
            content = content[4:].lstrip()

        # Try JSON parsing first, fall back to ast.literal_eval
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            import ast
            data = ast.literal_eval(content)

        # Validate structure
        if isinstance(data, dict) and set(data.keys()) == set(response_format.keys()):
            return data

        logger.warning(f"Response structure mismatch. Expected: {list(response_format.keys())}, Got: {list(data.keys())}")
        return fallback

    except (KeyError, json.JSONDecodeError, ValueError, SyntaxError) as e:
        logger.error(f"Failed to parse LLM response: {e}")
        return fallback
