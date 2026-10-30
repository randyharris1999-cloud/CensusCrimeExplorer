"""Build the two pages from shared code.
  desktop.src.html + app.js -> index.html   (desktop; sends phones to mobile.html)
  mobile.src.html  + app.js -> mobile.html  (phone layout)
Also writes artifact-*.html (same pages without the document wrapper) for claude.ai previews."""
import os
here = os.path.dirname(os.path.abspath(__file__)); root = os.path.join(here, "..")
rd = lambda f: open(os.path.join(here, f), encoding="utf-8").read()
css, js = rd("leaflet.css"), rd("app.js")
HEAD = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
        '<style>:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}body{margin:0}[hidden]{display:none!important}</style>\n')
for src, out, art in [("desktop.src.html", "index.html", "artifact-desktop.html"), ("mobile.src.html", "mobile.html", "artifact-mobile.html")]:
    body = rd(src).replace("/*LEAFLET_CSS*/", css).replace("/*APP_JS*/", js)
    i = body.index("</style>", body.index(":root{")) + len("</style>")
    open(os.path.join(root, out), "w", encoding="utf-8").write(HEAD + body[:i] + "\n</head>\n<body>\n" + body[i:] + "\n</body>\n</html>\n")
    open(os.path.join(here, art), "w", encoding="utf-8").write(body)
print("built index.html and mobile.html")
