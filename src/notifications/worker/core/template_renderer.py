from jinja2 import Environment, select_autoescape

env = Environment(
    autoescape=select_autoescape(default_for_string=True, default=True),
    enable_async=False,
)


def render_html_template(template_str: str, context: dict) -> str:
    template = env.from_string(template_str)
    return template.render(**context)


def render_text_template(template_str: str, context: dict) -> str:
    return render_html_template(template_str, context)
