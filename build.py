"""Build the CS336 lecture notes.

Each lecture's content lives in src/lecture_NN.html as a fragment:
a <!--meta {...json...} --> header followed by <section> elements
(each with an id and an <h2>), plus an optional trailing <script>.
This script wraps every fragment with the shared stylesheet, header,
table of contents and navigation, and writes standalone pages to
lectures/lecture_NN.html, plus the course hub at index.html.

Usage: python3 build.py
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT / "src"
OUT = ROOT / "lectures"

FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
    '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700'
    '&family=Noto+Serif+SC:wght@600;700&family=JetBrains+Mono:wght@400;600&display=swap">'
)

TOC_JS = """<script>
(function () {
  var tocD = document.getElementById("toc-details");
  if (tocD && window.matchMedia("(max-width: 900px)").matches) tocD.open = false;
  var links = Array.prototype.slice.call(document.querySelectorAll(".toc a"));
  var targets = links.map(function (a) { return document.getElementById(a.getAttribute("href").slice(1)); });
  function onScroll() {
    var cur = 0;
    for (var i = 0; i < targets.length; i++) {
      if (targets[i] && targets[i].getBoundingClientRect().top < 120) cur = i;
    }
    links.forEach(function (a, i) { a.classList.toggle("active", i === cur); });
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();
})();
</script>"""


def strip_tags(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def load(path):
    text = path.read_text()
    m = re.match(r"\s*<!--meta\s*(\{.*?\})\s*-->\s*", text, re.S)
    if not m:
        raise SystemExit(f"{path}: missing <!--meta {{...}} --> header")
    meta = json.loads(m.group(1))
    body = text[m.end():]
    script = ""
    i = body.rfind("<script>")
    if i != -1 and body.rstrip().endswith("</script>"):
        body, script = body[:i], body[i:]
    return meta, body, script


def build_toc(body):
    """Nested TOC from <section id><h2> and <h3 id> in document order."""
    items = []  # (level, id, label)
    for m in re.finditer(r'<section id="([^"]+)"[^>]*>\s*<h2>(.*?)</h2>|<h3 id="([^"]+)">(.*?)</h3>', body, re.S):
        if m.group(1):
            h2 = m.group(2)
            num = re.search(r'<span class="num">(.*?)</span>', h2)
            label = strip_tags(re.sub(r'<span class="num">.*?</span>', "", h2))
            if num:
                label = f"{int(num.group(1))}. {label}" if num.group(1).isdigit() else label
            items.append((2, m.group(1), label))
        else:
            items.append((3, m.group(3), strip_tags(m.group(4))))
    out = ["<ol>"]
    open_sub = False
    for i, (lvl, id_, label) in enumerate(items):
        if lvl == 2:
            if open_sub:
                out.append("</ol></li>")
                open_sub = False
            nxt = items[i + 1][0] if i + 1 < len(items) else 2
            if nxt == 3:
                out.append(f'<li><a href="#{id_}">{html.escape(label)}</a><ol>')
                open_sub = True
            else:
                out.append(f'<li><a href="#{id_}">{html.escape(label)}</a></li>')
        else:
            out.append(f'<li><a href="#{id_}">{html.escape(label)}</a></li>')
    if open_sub:
        out.append("</ol></li>")
    out.append("</ol>")
    return "\n".join(out)


def page(meta, body, script, css, prev_meta, next_meta, prefix):
    n = meta["num"]
    title = f"CS336 第{n}课笔记"
    nav = []
    if prev_meta:
        nav.append(f'<a href="{prefix}lecture_{prev_meta["num"]:02d}.html">← 第{prev_meta["num"]}课 {html.escape(prev_meta["short"])}</a>')
    if next_meta:
        nav.append(f'<a href="{prefix}lecture_{next_meta["num"]:02d}.html">第{next_meta["num"]}课 {html.escape(next_meta["short"])} →</a>')
    metas = "".join(f"<span><b>{html.escape(k)}</b> {html.escape(v)}</span>" for k, v in meta.get("meta", {}).items())
    return f"""<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
{FONTS}
<style>
{css}
</style>

<nav class="topbar" aria-label="课程导航">
  <a class="home" href="../index.html">CS336 · 全部笔记</a>
  <div class="pn">{''.join(nav)}</div>
</nav>

<header class="masthead">
  <div class="eyebrow">Stanford CS336 · Spring 2026 · Lecture {n}</div>
  <h1>{meta["title"]}</h1>
  <p class="lede">{meta["lede"]}</p>
  <div class="meta">{metas}</div>
</header>

<div class="layout">
  <nav class="toc" aria-label="目录">
    <details id="toc-details" open>
      <summary>目录</summary>
{build_toc(body)}
    </details>
  </nav>
  <main>
{body.strip()}
  </main>
</div>

<footer class="end">根据 Stanford CS336 Spring 2026 公开讲义 {html.escape(meta["source"])} 整理的学习笔记。标注为“第一性原理”“补充”的内容是笔记作者的推导和解释，不在原讲义中。<br>{' · '.join(nav)}</footer>

{TOC_JS}
{script.strip()}
"""


def index_page(metas, css):
    rows = []
    for m in metas:
        rows.append(f"""<a class="lec" href="lectures/lecture_{m['num']:02d}.html">
  <span class="n">{m['num']:02d}</span>
  <span class="t"><b>{m['title']}</b><span>{m['question']}</span></span>
  <span class="u">{html.escape(m['unit'])}</span>
</a>""")
    return f"""<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CS336 课程笔记</title>
{FONTS}
<style>
{css}
.hub {{ max-width: 860px; margin: 0 auto; }}
.lecs {{ display: grid; gap: 0; margin: 8px 0 32px; border-top: 1px solid var(--line); }}
.lec {{
  display: grid; grid-template-columns: 44px minmax(0, 1fr) auto; gap: 16px; align-items: baseline;
  padding: 14px 4px; border-bottom: 1px solid var(--line); text-decoration: none; color: var(--ink);
}}
.lec:hover {{ background: var(--surface); }}
.lec .n {{ font-family: var(--mono); font-size: 14px; color: var(--accent); font-weight: 600; }}
.lec .t {{ display: grid; gap: 2px; }}
.lec .t b {{ font-size: 16.5px; font-weight: 700; line-height: 1.5; }}
.lec .t span {{ font-size: 14px; color: var(--ink-2); line-height: 1.6; }}
.lec .u {{ font-family: var(--mono); font-size: 12px; color: var(--ink-3); white-space: nowrap; }}
@media (max-width: 560px) {{ .lec {{ grid-template-columns: 36px minmax(0, 1fr); }} .lec .u {{ grid-column: 2; }} }}
</style>

<header class="masthead hub">
  <div class="eyebrow">Stanford CS336 · Spring 2026</div>
  <h1>从零构建语言模型：课程笔记</h1>
  <p class="lede">CS336 全部 {len(metas)} 讲的中文详解笔记。每一讲先从第一性原理提出核心问题，再沿讲义展开推导，最后给出要点和自测题。</p>
  <div class="meta"><span><b>讲义来源</b> github.com/stanford-cs336/lectures</span><span><b>课程网站</b> stanford-cs336.github.io/spring2026</span></div>
</header>
<main class="hub">
  <p class="muted" style="margin-top:20px">每行下方的一句话，是这一讲要回答的核心问题。</p>
  <div class="lecs">
{chr(10).join(rows)}
  </div>
</main>
<footer class="end">学习笔记，内容依据 Stanford CS336 Spring 2026 公开讲义整理；“第一性原理”“补充”部分为笔记作者的推导。</footer>
"""


APP_JS = """<script>
(function () {
  var view = document.getElementById("view");
  var home = document.getElementById("home");
  var cache = {};

  function showHome() {
    view.hidden = true; view.innerHTML = ""; home.hidden = false;
    document.title = "CS336 课程笔记";
  }

  function rewrite(root) {
    root.querySelectorAll("a[href]").forEach(function (a) {
      var h = a.getAttribute("href");
      var m = h.match(/^lecture_(\\d\\d)\\.html$/);
      if (m) a.setAttribute("href", "#l" + m[1]);
      else if (h === "../index.html") a.setAttribute("href", "#");
    });
  }

  function mount(html) {
    var doc = new DOMParser().parseFromString(html, "text/html");
    view.innerHTML = "";
    [".topbar", ".masthead", ".layout", "footer.end"].forEach(function (sel) {
      var el = doc.querySelector(sel);
      if (el) view.appendChild(document.importNode(el, true));
    });
    rewrite(view);
    home.hidden = true; view.hidden = false;
    document.title = doc.title;
    window.scrollTo(0, 0);
    doc.querySelectorAll("script").forEach(function (old) {
      var s = document.createElement("script");
      s.textContent = old.textContent;
      view.appendChild(s);
    });
  }

  function route() {
    var m = location.hash.match(/^#l(\\d\\d)$/);
    if (!m) { showHome(); return; }
    var url = "lectures/lecture_" + m[1] + ".html";
    if (cache[url]) { mount(cache[url]); return; }
    fetch(url).then(function (r) {
      if (!r.ok) throw new Error(r.status);
      return r.text();
    }).then(function (t) { cache[url] = t; mount(t); }).catch(function () {
      view.hidden = false; home.hidden = true;
      view.innerHTML = '<p class="muted" style="max-width:760px;margin:40px auto">这一讲没能加载出来。请刷新页面再试一次，或 <a href="#">返回目录</a>。</p>';
    });
  }

  // In-page anchors (table of contents) scroll instead of changing the route.
  document.addEventListener("click", function (e) {
    var a = e.target.closest && e.target.closest('a[href^="#"]');
    if (!a) return;
    var h = a.getAttribute("href");
    if (h === "#" || /^#l\\d\\d$/.test(h)) return;
    var t = document.getElementById(h.slice(1));
    if (t) { e.preventDefault(); t.scrollIntoView({ behavior: "smooth", block: "start" }); }
  });
  window.addEventListener("hashchange", route);
  route();
})();
</script>"""


def app_page(metas, css, index_html):
    """Single-page shell for the published artifact: the course index plus a
    view that fetches each lecture page (published alongside) and swaps it in."""
    body = index_html.split("</style>", 1)[1]
    body = re.sub(r'href="lectures/lecture_(\d\d)\.html"', r'href="#l\1"', body)
    head = index_html.split("</style>", 1)[0] + "</style>"
    return f'{head}\n<div id="home">\n{body}\n</div>\n<div id="view" hidden></div>\n{APP_JS}\n'


def main():
    css = (SRC / "style.css").read_text().strip()
    files = sorted(SRC.glob("lecture_*.html"))
    loaded = [load(f) for f in files]
    metas = [m for m, _, _ in loaded]
    OUT.mkdir(exist_ok=True)
    for i, (meta, body, script) in enumerate(loaded):
        prev_meta = metas[i - 1] if i > 0 else None
        next_meta = metas[i + 1] if i + 1 < len(metas) else None
        out = OUT / f"lecture_{meta['num']:02d}.html"
        out.write_text(page(meta, body, script, css, prev_meta, next_meta, ""))
        print("wrote", out.relative_to(ROOT))
    index_html = index_page(metas, css)
    (ROOT / "index.html").write_text(index_html)
    print("wrote index.html")
    site = ROOT / "site"
    site.mkdir(exist_ok=True)
    (site / "app.html").write_text(app_page(metas, css, index_html))
    print("wrote site/app.html (artifact shell)")


if __name__ == "__main__":
    main()
