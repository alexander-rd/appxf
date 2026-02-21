# AI generated helpers

## Build documentation locally

Install the documentation dependencies:

```bash
pip install -r doc/requirements.txt
```

Build the HTML documentation:

```bash
sphinx-build -M html doc doc/_build
```

Open the generated start page:

`doc/_build/html/index.html`

## Warning triage (recommended workflow)

Start with warnings that affect navigation and readability first.

1. `toc.no_title`
	- Cause: a page has no top-level title.
	- Fix: add one H1 heading (`# Title`) at the start of the file.
2. `toc.not_included`
	- Cause: page exists but is not part of any `toctree`.
	- Fix: include it in the relevant section index (for example `features/index.md`).
3. `myst.header`
	- Cause: heading levels jump (for example H1 to H3).
	- Fix: normalize heading hierarchy to be consecutive.
4. `image.not_readable`
	- Cause: broken relative image path.
	- Fix: correct path or move image to `doc/images` and update link.
5. `misc.highlighting_failure`
	- Cause: unknown code block lexer (for example `plantuml`).
	- Fix: use `text` for now or add proper rendering support later.

Useful check command:

```bash
.venv/bin/python -m sphinx -M html doc doc/_build
```

## Navigation structure in this setup

- Root `index.md` contains only top-level pages and section entry points.
- Section pages (`features/index.md`, `modules/index.md`, `matema_features/index.md`, `matema_modules/index.md`) own their subtrees.
- `toctree` uses `:titlesonly:` and `:maxdepth: 1` to avoid sidebar clutter.

If you later want collapsible tree behavior, switching to `sphinx_rtd_theme` or `sphinx_book_theme` is the common next step.

### Optional: collapsible navigation (draft)

1. Add theme package to `doc/requirements.txt`:
   - `sphinx-rtd-theme`
2. In `doc/conf.py` set:

```python
html_theme = 'sphinx_rtd_theme'
html_theme_options = {
	'collapse_navigation': True,
	'navigation_depth': 2,
}
```

This keeps the main groups visible while allowing subtree expansion on demand.
