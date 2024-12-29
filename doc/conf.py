# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
from importlib.metadata import version as _version
from sphinxawesome_theme.postprocess import Icons

release = '.'.join(_version('OZI.build').split('.')[:2])

project = 'OZI.build'
copyright = '2024, Thibault Saunier, Eden Ross Duff MSc'
author = 'Thibault Saunier, Eden Ross Duff MSc'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_static_path = ['_static']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
extensions = [
    'invocations.autodoc',
    'myst_parser',
    'sphinx.ext.autodoc',
    'sphinx.ext.coverage',
    'sphinx.ext.duration',
    'sphinx.ext.extlinks',
    'sphinx.ext.githubpages',
    'sphinx.ext.ifconfig',
    'sphinx.ext.intersphinx',
    'sphinx.ext.napoleon',
    'sphinx.ext.todo',
    'sphinx.ext.viewcode',
    'sphinxemoji.sphinxemoji',
    'sphinx_design',
    'sphinx_last_updated_by_git',
    'sphinx_sitemap',
    'sphinxawesome_theme.highlighting',
    'sphinxcontrib.programoutput',
    'sphinxcontrib.cairosvgconverter',
]
templates_path = ['_templates']
today_fmt = '%d-%b-%Y'
python_display_short_literal_types = True

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output
html_title = 'build.OZIproject.dev'
html_theme = 'sphinxawesome_theme'
html_context = {'mode': 'production'}
# Set canonical URL from the Read the Docs Domain
html_baseurl = os.environ.get("READTHEDOCS_CANONICAL_URL", "")

# Tell Jinja2 templates the build is running on Read the Docs
if os.environ.get("READTHEDOCS", "") == "True":
    html_context["READTHEDOCS"] = True

html_baseurl = 'https://oziproject.dev/'
html_static_path = ['_static']
html_css_files = ['css/custom.css']
html_extra_path = ['robots.txt']
html_permalinks_icon = Icons.permalinks_icon

# -- Options for LaTeX output ------------------------------------------------
latex_engine = 'lualatex'
latex_elements = {
    'preamble': r'''\directlua {
  luaotfload.add_fallback("emoji",
  {
     "[TwemojiMozilla.ttf]:mode=harf;",
     "[DejaVuSans.ttf]:mode=harf;",
  } 
  )
}
\setmainfont{LatinModernRoman}[RawFeature={fallback=emoji},SmallCapsFont={* Caps}]
\setsansfont{LatinModernSans}[RawFeature={fallback=emoji}]
\setmonofont{DejaVuSansMono}[RawFeature={fallback=emoji},Scale=0.8]
''',
    'fncychap': r'\usepackage[Sonny]{fncychap}'
}
latex_show_pagerefs = True
latex_show_urls = 'inline'
latex_theme = 'howto'

# -- sphinx.ext.autodoc ------------------------------------------------------
autodoc_preserve_defaults = True
autodoc_typehints_format = 'short'

# -- sphinx.ext.coverage -----------------------------------------------------
coverage_show_missing_items = True

# -- sphinx.ext.intersphinx --------------------------------------------------
intersphinx_mapping = {
    'devguide': ('https://devguide.python.org', None),
    'pip': ('https://pip.pypa.io/en/latest', None),
    'pipx': ('https://pipx.pypa.io/stable/', None),
    'pip-tools': ('https://pip-tools.readthedocs.io/en/stable/', None),
    'pypa': ('https://packaging.python.org', None),
    'python': ('https://docs.python.org/3.10/', None),
    'pytest': ('https://docs.pytest.org/en/stable/', None),
    'bandit': ('https://bandit.readthedocs.io/en/1.7.5/', None),
    'jinja2': ('https://jinja.palletsprojects.com/en/3.1.x/', None),
    'semantic_release': (
        'https://python-semantic-release.readthedocs.io/en/stable/',
        None,
    ),
    'setuptools': ('https://setuptools.pypa.io/en/stable/', None),
    'tox': ('https://tox.wiki/en/stable/', None)
}

myst_enable_extensions = ['colon_fence']