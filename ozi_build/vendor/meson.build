sources = ['pyc_wheel/src/pyc_wheel/__about__.py', 'pyc_wheel/src/pyc_wheel/__init__.py', 'pyc_wheel/src/pyc_wheel/__main__.py', 'pyc_wheel/src/pyc_wheel/_pyc_wheel.py']
foreach source: sources
    fs.copyfile(source)
    python.install_sources(
        source,
        pure : true,
        subdir : 'ozi_build' / 'vendor'
    )
endforeach