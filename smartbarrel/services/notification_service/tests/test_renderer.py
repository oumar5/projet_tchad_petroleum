from services.notification_service.app.services.template_renderer import render


def test_render_simple():
    out = render("Hello {{ name }}", {"name": "Oumar"})
    assert out == "Hello Oumar"


def test_render_escapes_html():
    out = render("{{ x }}", {"x": "<script>alert(1)</script>"})
    assert "&lt;script&gt;" in out
