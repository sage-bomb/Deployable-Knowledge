from typing import Dict, Any
from .user_settings import get_prompt_template, list_prompt_templates, load_settings
from .llm_factory import make_llm

def render_prompt(template: dict, vars: Dict[str, Any]) -> str:
    # Minimal formatter; supports {var} placeholders in 'system' and/or 'content'
    system = (template.get("system") or "").format(**vars)
    content = (template.get("content") or "").format(**vars)
    prompt = (system + "\n\n" + content).strip() if system else content
    return prompt

def generate_reply(user_id: str, vars: Dict[str, Any]) -> str:
    settings = load_settings(user_id)
    tmpl = None
    if settings.prompt_template_id:
        pt = get_prompt_template(settings.prompt_template_id)
        if pt:
            tmpl = pt.model_dump()
    if not tmpl:
        tmpl = {"content": "{message}"}  # trivial fallback template
    prompt = render_prompt(tmpl, vars)
    llm = make_llm(settings.llm_provider, settings.llm_model or None)
    return llm.generate(prompt)
