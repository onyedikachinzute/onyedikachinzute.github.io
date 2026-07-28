#!/usr/bin/env python3
"""
add_project.py
--------------
Interactive tool for adding a new project to the portfolio site.

Run it from the root of your portfolio repo (same folder as index.html):

    python add_project.py

It will:
  1. Ask for a GitHub repo URL and pull the description/language from the API
  2. Ask you a handful of quick questions (title, tags, featured or not, etc.)
  3. Generate projects/<slug>.html from a built-in template
  4. Create projects/screenshots/<slug>/ so you can drop in 01.jpg..04.jpg later
  5. Insert a card into index.html (Featured Projects and/or All Projects)
  6. Add the new page to sitemap.xml
  7. Re-chain the "next project" links across all detail pages so the loop
     stays connected

Only uses the Python standard library — no pip installs required.
"""

import json
import os
import re
import sys
import urllib.request
import urllib.error

SITE_URL = "https://onyedikachinzute.github.io"
# This script lives in tools/, so the repo root is its parent directory.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_PATH = os.path.join(ROOT, "index.html")
SITEMAP_PATH = os.path.join(ROOT, "sitemap.xml")
MANIFEST_PATH = os.path.join(ROOT, "project_manifest.json")
PROJECTS_DIR = os.path.join(ROOT, "projects")

FEATURED_MARKER = "<!-- FEATURED_PROJECTS_INSERT -->"
ALL_PROJECTS_MARKER = "<!-- ALL_PROJECTS_INSERT -->"
SITEMAP_MARKER = "<!-- SITEMAP_INSERT -->"

ICON_LIBRARY = {
    "1": ("Code brackets", '<path d="M8 5 3 12l5 7M16 5l5 7-5 7"/>'),
    "2": ("Database", '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 9h18"/><rect x="6" y="12" width="3" height="3" rx=".5"/><rect x="10.5" y="12" width="3" height="3" rx=".5"/>'),
    "3": ("AI / robot", '<rect x="5" y="7" width="14" height="11" rx="3"/><path d="M12 7V4M9 3.5h6"/><circle cx="9" cy="12.5" r="1.1" fill="currentColor" stroke="none"/><circle cx="15" cy="12.5" r="1.1" fill="currentColor" stroke="none"/>'),
    "4": ("Web / browser", '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 9h18"/><circle cx="6" cy="6.5" r=".6" fill="currentColor" stroke="none"/>'),
    "5": ("Checklist", '<rect x="4" y="4" width="16" height="16" rx="2"/><path d="M8 10l2 2 4-4"/><path d="M8 16h6"/>'),
    "6": ("Camera / vision", '<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="10" r="2.2"/><path d="M4 18l4.5-4.5a1.5 1.5 0 0 1 2.1 0L14 17"/>'),
}

GLYPH_HINTS = {
    "1": "CODE", "2": "DB", "3": "AI", "4": "WEB", "5": "APP", "6": "CV",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def ask(prompt, default=None, required=False):
    suffix = f" [{default}]" if default else ""
    while True:
        val = input(f"{prompt}{suffix}: ").strip()
        if not val and default is not None:
            return default
        if not val and required:
            print("  This one's required — give it a shot.")
            continue
        return val


def ask_multiline(prompt):
    print(f"{prompt} (multiple lines OK, blank line to finish):")
    lines = []
    while True:
        line = input("  ").strip()
        if not line:
            break
        lines.append(line)
    return " ".join(lines)


def ask_yes_no(prompt, default=True):
    d = "Y/n" if default else "y/N"
    val = input(f"{prompt} [{d}]: ").strip().lower()
    if not val:
        return default
    return val.startswith("y")


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "portfolio-add-project"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_text(url):
    req = urllib.request.Request(url, headers={"User-Agent": "portfolio-add-project"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse_github_url(url):
    m = re.search(r"github\.com/([^/]+)/([^/#?]+)", url)
    if not m:
        return None, None
    owner, repo = m.group(1), m.group(2)
    repo = repo.rstrip("/").removesuffix(".git")
    return owner, repo


def fetch_readme(owner, repo, default_branch):
    for branch in (default_branch, "main", "master"):
        try:
            return fetch_text(f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/README.md")
        except urllib.error.HTTPError:
            continue
        except Exception:
            continue
    return ""


def extract_bullets(readme_text, limit=6):
    """Best-effort pull of '- ' bullet lines from a README for feature suggestions."""
    lines = readme_text.splitlines()
    bullets = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(("- ", "* ")) and len(stripped) > 4:
            clean = re.sub(r"[*_`#]", "", stripped[2:]).strip()
            clean = re.sub(r"^[^\w]+", "", clean)  # strip leading emoji/symbols
            if clean and len(clean) < 160:
                bullets.append(clean)
        if len(bullets) >= limit:
            break
    return bullets


def load_manifest():
    if os.path.exists(MANIFEST_PATH):
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"projects": []}


def save_manifest(manifest):
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

DETAIL_PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{title} — Case Study | Kachi Nzute</title>
<meta name="description" content="{description}" />
<link rel="canonical" href="{site_url}/projects/{slug}.html" />
<meta property="og:type" content="article" />
<meta property="og:title" content="{title} — Case Study | Kachi Nzute" />
<meta property="og:description" content="{description}" />
<meta property="og:url" content="{site_url}/projects/{slug}.html" />
<meta property="og:image" content="{site_url}/images/kachi.jpg" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="{title} — Case Study | Kachi Nzute" />
<meta name="twitter:description" content="{description}" />
<meta name="twitter:image" content="{site_url}/images/kachi.jpg" />
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="../style.css" />
<link rel="icon" type="image/x-icon" href="../Kachi.ico">
<script>
  (function(){{
    try {{
      var saved = localStorage.getItem('theme');
      if (saved === 'light') document.documentElement.setAttribute('data-theme', 'light');
    }} catch(e){{}}
  }})();
</script>
<script defer src="../script.js"></script>
</head>
<body>
<div class="scan-noise" aria-hidden="true"></div>

<header class="site-header" id="siteHeader">
  <nav class="nav container">
    <a class="brand" href="../index.html#home">Kachi<span class="dot">.</span><span class="brand-tag">dev</span></a>
    <button id="hamburger" class="hamburger" aria-label="Open menu" aria-expanded="false">
      <span class="ham-line"></span><span class="ham-line"></span><span class="ham-line"></span>
    </button>
    <ul class="nav-list" id="navList">
      <li><a href="../index.html#home" class="nav-link">Home</a></li>
      <li><a href="../index.html#work" class="nav-link">Projects</a></li>
      <li><a href="../index.html#experience" class="nav-link">Experience</a></li>
      <li><a href="../index.html#skills" class="nav-link">Skills</a></li>
      <li><a href="../index.html#about" class="nav-link">About</a></li>
      <li><a href="../index.html#contact" class="nav-link">Contact</a></li>
    </ul>
  </nav>
</header>

<main>
  <section class="detail-hero container">
    <div class="breadcrumb">
      <a href="../index.html">Home</a><span>/</span><a href="../index.html#all-projects">All Projects</a><span>/</span><span>{title}</span>
    </div>

    <div class="detail-head">
      <div>
        <h1 class="detail-title">{title}</h1>
        <p class="detail-subtitle mono">{subtitle}</p>
      </div>
      <div class="detail-actions">
        <a class="btn ghost" href="{github_url}" target="_blank" rel="noopener">View on GitHub</a>
        <a class="btn primary" href="../index.html#contact">Get in Touch</a>
      </div>
    </div>

    <div class="detail-tags">
      {tags_html}
    </div>
  </section>

  <section class="detail-body container">
    <div class="detail-main">
      <h2>Overview</h2>
      <p>{description}</p>

      <h2>The Idea</h2>
      <p>{idea}</p>

      <div class="shot-section">
        <h2>Screenshots</h2>
        <div class="shot-gallery empty" data-shots='{shots_json}'></div>
      </div>

      <h2>How It Works</h2>
      <ul>
{how_it_works_html}
      </ul>

      <h2>Features</h2>
      <ul>
{features_html}
      </ul>

      <h2>What's Next</h2>
      <p>{whats_next}</p>

      <h2>Getting started</h2>
      <div class="code-block">
<span class="cm"># running it locally</span><br>
git clone {github_url}.git<br>
cd {repo_name}<br>
<span class="cm"># see the repo README for setup &amp; run instructions</span>
      </div>

      <a class="next-project" href="{next_slug}.html">
        <div>
          <span class="np-label">Next project</span>
          <span class="np-name">{next_title} →</span>
        </div>
      </a>
    </div>

    <aside class="detail-side">
      <div class="side-card">
        <h3>Project Info</h3>
        <div class="side-row"><span class="k">Role</span><span class="v">Sole Developer</span></div>
        <div class="side-row"><span class="k">Context</span><span class="v">Personal Project</span></div>
        <div class="side-row"><span class="k">Primary Language</span><span class="v">{primary_language}</span></div>
      </div>
      <div class="side-card">
        <h3>Tech Stack</h3>
        <div class="side-stack">
          {tags_html}
        </div>
      </div>
      <div class="side-card">
        <h3>Links</h3>
        <div class="side-stack">
          <a class="btn ghost small" style="width:100%; justify-content:center;" href="{github_url}" target="_blank" rel="noopener">Source on GitHub</a>
        </div>
      </div>
    </aside>
  </section>

  <footer class="site-footer">
    <div class="container footer-row">
      <p>© <span id="yr"></span> Onyedikachi Nzute. All rights reserved.</p>
      <div class="footer-links">
        <a href="https://github.com/onyedikachinzute/" target="_blank">GitHub</a>
        <a href="https://ng.linkedin.com/in/onyedikachi-nzute-b30162331" target="_blank">LinkedIn</a>
        <a href="mailto:onyedikachinzute@gmail.com">Email</a>
      </div>
    </div>
  </footer>
</main>

<a href="#home" id="backToTop" class="back-to-top" aria-label="Back to top">↑</a>
<button id="themeToggle" class="theme-toggle" aria-label="Switch to light mode" type="button">
  <svg class="icon-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
  <svg class="icon-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>
</button>
</body>
</html>
"""

FEATURED_CARD_TEMPLATE = """      <a class="project-card reveal" href="projects/{slug}.html">
        <div class="pc-visual" data-shot="projects/screenshots/{slug}/01">
          <span class="pc-glyph mono">{glyph}</span>
          <span class="corner tl"></span><span class="corner br"></span>
          <div class="icon-badge">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
              {icon_paths}
            </svg>
          </div>
          <svg class="pc-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4">
            {icon_paths}
          </svg>
          <span class="pc-status">{status}</span>
        </div>
        <div class="pc-body">
          <span class="pc-index mono">{index}</span>
          <h3 class="pc-title">{title}</h3>
          <p class="pc-subtitle">{subtitle}</p>
          <p class="pc-desc">{description}</p>
          <div class="pc-tags">{tags_html}</div>
          <div class="pc-actions">
            <span class="pc-link filled">View Case Study
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M13 6l6 6-6 6"/></svg>
            </span>
            <span class="pc-link">GitHub
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18c-4.5 2-4.5-1-6-2m12 4v-3.4c0-.9.3-1.5.7-1.8-2.3-.3-4.7-1.2-4.7-5.2 0-1.1.4-2 1-2.7-.1-.3-.4-1.4.1-2.9 0 0 .9-.3 3 1a10 10 0 0 1 5.4 0c2.1-1.3 3-1 3-1 .5 1.5.2 2.6.1 2.9.6.7 1 1.6 1 2.7 0 4-2.4 4.9-4.7 5.2.4.3.7.9.7 1.8V19"/></svg>
            </span>
          </div>
        </div>
      </a>

"""

MINI_CARD_TEMPLATE = """      <a class="mini-card" href="projects/{slug}.html">
        <span class="corner tl"></span><span class="corner br"></span>
        <span class="mini-card-glyph">{glyph}</span>
        <div class="mini-card-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">
            {icon_paths}
          </svg>
        </div>
        <h3>{title}</h3>
        <p class="mini-subtitle">{subtitle}</p>
        <p class="mini-desc">{short_description}</p>
        <div class="mini-tags">{mini_tags_html}</div>
        <div class="mini-card-foot">
          <span>View project</span>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M13 6l6 6-6 6"/></svg>
        </div>
      </a>

"""

SITEMAP_ENTRY_TEMPLATE = """  <url>
    <loc>{site_url}/projects/{slug}.html</loc>
    <changefreq>monthly</changefreq>
    <priority>{priority}</priority>
  </url>
  """


# ---------------------------------------------------------------------------
# Main flow
# ---------------------------------------------------------------------------

def main():
    print("\n=== Add a new project to your portfolio ===\n")

    if not os.path.exists(INDEX_PATH):
        print("ERROR: index.html not found here. Run this script from your portfolio repo root.")
        sys.exit(1)

    repo_url = ask("GitHub repo URL", required=True)
    owner, repo = parse_github_url(repo_url)
    if not owner:
        print("Couldn't parse that as a GitHub URL. Expected something like:")
        print("  https://github.com/username/repo-name")
        sys.exit(1)

    github_url = f"https://github.com/{owner}/{repo}"
    print(f"\nFetching repo info for {owner}/{repo} ...")

    api_data = {}
    try:
        api_data = fetch_json(f"https://api.github.com/repos/{owner}/{repo}")
    except Exception as e:
        print(f"  (Couldn't reach the GitHub API: {e} — you'll just fill things in manually.)")

    default_branch = api_data.get("default_branch", "main")
    gh_description = api_data.get("description") or ""
    primary_language = api_data.get("language") or "Python"
    topics = api_data.get("topics") or []

    readme = ""
    try:
        readme = fetch_readme(owner, repo, default_branch)
    except Exception:
        pass

    suggested_bullets = extract_bullets(readme) if readme else []

    print("\n--- Basic info ---")
    default_title = repo.replace("-", " ").replace("_", " ").title()
    title = ask("Project title", default=default_title, required=True)
    slug = slugify(ask("URL slug (used in the filename)", default=slugify(title)))
    subtitle = ask("One-line subtitle (shown under the title)", required=True)

    default_desc = gh_description or "A project built to solve a real, specific problem."
    description = ask("Short description (1-2 sentences)", default=default_desc, required=True)

    print("\n--- The Idea (why you built it / the problem it solves) ---")
    idea = ask_multiline("Describe the idea/motivation behind the project")
    if not idea:
        idea = description

    default_tags = ", ".join([primary_language] + topics[:4]) if topics else primary_language
    tags_raw = ask("Tags, comma-separated", default=default_tags, required=True)
    tags = [t.strip() for t in tags_raw.split(",") if t.strip()]

    print("\n--- How It Works (technical breakdown, shown as bullets) ---")
    how_it_works = []
    print("Enter how-it-works bullets one at a time. Blank line to finish.")
    while True:
        line = input(f"  Step {len(how_it_works) + 1}: ").strip()
        if not line:
            break
        how_it_works.append(line)
    if not how_it_works:
        how_it_works = ["Built with " + primary_language + "."]

    print("\n--- Features (for the 'Features' list on the detail page) ---")
    features = []
    if suggested_bullets:
        print("Found these candidate bullets in the README:")
        for i, b in enumerate(suggested_bullets, 1):
            print(f"  {i}. {b}")
        use_suggested = ask_yes_no("Use these as-is?", default=True)
        if use_suggested:
            features = suggested_bullets
    if not features:
        print("Enter feature bullets one at a time. Blank line to finish.")
        while True:
            line = input(f"  Feature {len(features) + 1}: ").strip()
            if not line:
                break
            features.append(line)
    if not features:
        features = [description]

    print("\n--- What's Next (future plans / roadmap) ---")
    whats_next = ask_multiline("What's next for this project")
    if not whats_next:
        whats_next = "Still actively maintained — more improvements planned as the project evolves."

    print("\n--- Card appearance ---")
    for key, (label, _) in ICON_LIBRARY.items():
        print(f"  {key}. {label}")
    icon_choice = ask("Pick an icon", default="1")
    if icon_choice not in ICON_LIBRARY:
        icon_choice = "1"
    icon_paths = ICON_LIBRARY[icon_choice][1]
    glyph_prefix = GLYPH_HINTS.get(icon_choice, "PRJ")

    manifest = load_manifest()
    existing_slugs = [p["slug"] for p in manifest["projects"]]
    if slug in existing_slugs:
        print(f"\nWARNING: slug '{slug}' already exists in project_manifest.json.")
        if not ask_yes_no("Continue anyway and overwrite?", default=False):
            print("Aborted.")
            sys.exit(0)

    glyph_num = str(len(manifest["projects"]) + 1).zfill(2)
    glyph = f"{glyph_prefix}-{glyph_num}"
    status = ask("Status badge text (shown on the Featured card)", default="Personal project")

    is_featured = ask_yes_no("\nShow this in the big Featured Projects section?", default=False)

    # ---- Build shots_json ----
    # No extension baked in here — script.js tries multiple extensions per
    # slot at load time, so you can mix .png and .jpg freely across shots.
    shots = [f"screenshots/{slug}/0{i}" for i in range(1, 5)]
    shots_json = json.dumps(shots)

    # ---- Determine next-project chain ----
    prev_slug = manifest["projects"][-1]["slug"] if manifest["projects"] else None
    first_slug = manifest["projects"][0]["slug"] if manifest["projects"] else slug
    first_title = manifest["projects"][0]["title"] if manifest["projects"] else title

    # ---- Write detail page ----
    os.makedirs(PROJECTS_DIR, exist_ok=True)
    detail_path = os.path.join(PROJECTS_DIR, f"{slug}.html")

    tags_html_detail = "".join(f"<span>{t}</span>\n      " for t in tags).strip()
    features_html = "\n".join(f"        <li><strong>{f.split(':')[0].strip()}</strong>{':' + f.split(':',1)[1] if ':' in f else ''}</li>" if ':' in f else f"        <li>{f}</li>" for f in features)
    how_it_works_html = "\n".join(f"        <li>{s}</li>" for s in how_it_works)

    detail_html = DETAIL_PAGE_TEMPLATE.format(
        title=title,
        subtitle=subtitle,
        description=description,
        idea=idea,
        site_url=SITE_URL,
        slug=slug,
        github_url=github_url,
        repo_name=repo,
        tags_html=tags_html_detail,
        how_it_works_html=how_it_works_html,
        features_html=features_html,
        whats_next=whats_next,
        shots_json=shots_json,
        primary_language=primary_language,
        next_slug=first_slug,
        next_title=first_title,
    )
    with open(detail_path, "w", encoding="utf-8") as f:
        f.write(detail_html)
    print(f"\n✓ Wrote {os.path.relpath(detail_path, ROOT)}")

    # ---- Re-point previous last project's next-project link to the new one ----
    if prev_slug:
        prev_path = os.path.join(PROJECTS_DIR, f"{prev_slug}.html")
        if os.path.exists(prev_path):
            with open(prev_path, "r", encoding="utf-8") as f:
                prev_html = f.read()
            new_prev_html = re.sub(
                r'<a class="next-project" href="[^"]+">\s*<div>\s*<span class="np-label">[^<]*</span>\s*<span class="np-name">[^<]*→</span>\s*</div>\s*</a>',
                f'<a class="next-project" href="{slug}.html">\n        <div>\n          <span class="np-label">Next project</span>\n          <span class="np-name">{title} →</span>\n        </div>\n      </a>',
                prev_html,
                count=1,
            )
            if new_prev_html != prev_html:
                with open(prev_path, "w", encoding="utf-8") as f:
                    f.write(new_prev_html)
                print(f"✓ Updated next-project link in {prev_slug}.html → {slug}.html")

    # ---- Screenshot folder ----
    shot_dir = os.path.join(PROJECTS_DIR, "screenshots", slug)
    os.makedirs(shot_dir, exist_ok=True)
    gitkeep = os.path.join(shot_dir, ".gitkeep")
    if not os.path.exists(gitkeep):
        open(gitkeep, "w").close()
    print(f"✓ Created {os.path.relpath(shot_dir, ROOT)}/ (drop 01.jpg..04.jpg in here)")

    # ---- Insert into index.html ----
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        index_html = f.read()

    tags_html_mini = "".join(f"<span>{t}</span>" for t in tags[:3])

    if is_featured:
        if FEATURED_MARKER not in index_html:
            print("WARNING: Featured insertion marker not found in index.html — skipping featured card insert.")
        else:
            featured_index = str(sum(1 for p in manifest["projects"] if p.get("featured")) + 1).zfill(2)
            card = FEATURED_CARD_TEMPLATE.format(
                slug=slug,
                glyph=glyph,
                icon_paths=icon_paths,
                status=status,
                index=featured_index,
                title=title,
                subtitle=subtitle,
                description=description,
                tags_html=tags_html_mini,
            ).lstrip()
            index_html = index_html.replace(FEATURED_MARKER, card + FEATURED_MARKER)
            print("✓ Inserted Featured Projects card")

    if ALL_PROJECTS_MARKER not in index_html:
        print("WARNING: All Projects insertion marker not found in index.html — skipping mini-card insert.")
    else:
        mini_card = MINI_CARD_TEMPLATE.format(
            slug=slug,
            glyph=glyph,
            icon_paths=icon_paths,
            title=title,
            subtitle=subtitle,
            short_description=description,
            mini_tags_html=tags_html_mini,
        ).lstrip()
        index_html = index_html.replace(ALL_PROJECTS_MARKER, mini_card + ALL_PROJECTS_MARKER)
        print("✓ Inserted All Projects card")

    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        f.write(index_html)

    # ---- Insert into sitemap.xml ----
    if os.path.exists(SITEMAP_PATH):
        with open(SITEMAP_PATH, "r", encoding="utf-8") as f:
            sitemap = f.read()
        if SITEMAP_MARKER in sitemap:
            entry = SITEMAP_ENTRY_TEMPLATE.format(site_url=SITE_URL, slug=slug, priority="0.8" if is_featured else "0.7").lstrip()
            sitemap = sitemap.replace(SITEMAP_MARKER, entry + SITEMAP_MARKER)
            with open(SITEMAP_PATH, "w", encoding="utf-8") as f:
                f.write(sitemap)
            print("✓ Added entry to sitemap.xml")
        else:
            print("WARNING: sitemap marker not found — skipping sitemap update.")

    # ---- Update manifest ----
    manifest["projects"].append({
        "slug": slug,
        "title": title,
        "featured": is_featured,
    })
    save_manifest(manifest)
    print("✓ Updated project_manifest.json")

    print("\n=== Done ===")
    print(f"New page: projects/{slug}.html")
    print(f"Add screenshots to: projects/screenshots/{slug}/01.png (or .jpg — up to 04, either format works)")
    print("\nWhen ready, push it live:")
    print("  git add .")
    print(f'  git commit -m "Add {title} project"')
    print("  git push origin main\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(0)