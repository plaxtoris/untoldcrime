from prompts import prompt_builder
import requests
import logging
import ast
import os


def prompt(model="zalazium-fast", word_limit=200, setting="Bitcoin Darknet"):
    response_format = {
        "story": "Hier kommt der Text der Geschichte hin.",
        "title": "Erzeuge ein Titel für die Geschichte mit maximal 5 Wörten",
        "summary": "Hoer kommt die Kurzfassung der Geschichte in etwa 30 Wörtern hin",
    }
    prompt_sys = prompt_builder(word_limit=word_limit, setting=setting)
    output = _prompt(model=model, prompt_sys=prompt_sys, prompt_usr=None, response_format=response_format)
    return output


def _prompt(model="zalazium-fast", prompt_sys=None, prompt_usr=None, response_format={}):
    try:
        # connection
        domain = os.environ.get("DOMAIN_WRAPPER")
        url = f"https://{domain}/v1/chat/completions"
        headers = {"Authorization": f"Bearer {os.environ.get('LITELLM_MASTER_KEY')}", "Content-Type": "application/json"}

        # messages
        if prompt_usr:
            messages = [{"role": "system", "content": prompt_sys}, {"role": "user", "content": prompt_usr}]
        else:
            messages = [{"role": "system", "content": prompt_sys}]

        # data
        data = {"model": model, "messages": messages}
        if response_format:
            data["response_format"] = _response_format(response_format)

        response = requests.post(url, headers=headers, json=data, timeout=600)
        response.raise_for_status()
        output = _sanitize(response=response, response_format=response_format)
        return output
    except Exception as e:
        logging.error(f">>> error in prompt: {e}")
        return None


def _response_format(response_format: dict) -> dict:
    properties = {}
    for key, value in response_format.items():
        properties[key] = {"description": value}

    return {
        "type": "json_schema",
        "json_schema": {"name": "response_schema", "schema": {"type": "object", "properties": properties, "required": list(response_format.keys()), "additionalProperties": False}},
    }


def _sanitize(response, response_format: dict):
    try:
        response_format_fallback = {key: "no_data" for key in response_format}
        content = response.json()["choices"][0]["message"]["content"].strip("` \n")
        if content.lower().startswith("json"):
            content = content[4:].lstrip()
        data = ast.literal_eval(content)
        if isinstance(data, dict) and set(data.keys()) == set(response_format.keys()):
            return data
        else:
            return response_format_fallback
    except Exception as e:
        logging.error(f"JSON decode failed: {e}")
        return response_format_fallback
