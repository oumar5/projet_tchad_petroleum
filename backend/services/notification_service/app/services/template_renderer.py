"""Jinja2 template rendering."""
from typing import Any

from jinja2 import Environment, StrictUndefined

_env = Environment(autoescape=True, undefined=StrictUndefined)


def render(template_str: str, variables: dict[str, Any]) -> str:
    return _env.from_string(template_str).render(**variables)
