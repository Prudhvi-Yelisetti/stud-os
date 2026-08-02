"""
Parses a provider's chat() reply as JSON, tolerating the common way
models wrap it in a markdown code fence despite being told not to.
Raises ValueError on anything that isn't valid JSON after that cleanup --
callers turn that into a clean error rather than a raw traceback.
"""
import json
import re

_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$")


def parse_json_reply(raw: str) -> dict:
    text = _FENCE.sub("", raw.strip()).strip()
    return json.loads(text)
