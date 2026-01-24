FORM12BB_HTML = """
<!doctype html>
<html>
<head><title>Form 12BB</title></head>
<body>
<h2>Form 12BB ({{ fy }})</h2>
<h3>Uploads</h3>
{{ uploads }}
</body>
</html>
"""

def render_form12bb(fy, uploads):
    items = "".join([
        f'<li>{u["filename"]} - <a href="{u["download_url"]}">Download</a></li>'
        for u in uploads
    ]) or "<p>No uploads</p>"

    return FORM12BB_HTML.replace("{{ fy }}", fy).replace("{{ uploads }}", items)
