sources = ['pyc_wheel/src/__about__.py', 'pyc_wheel/src/__init__.py', 'pyc_wheel/src/__main__.py', 'pyc_wheel/src/_pyc_wheel.py']
foreach source: sources
    fs.copyfile(source)
    python.install_sources(
        source,
        pure : true,
        subdir : 'ozi_build' / 'vendor' / 'pyc_wheel'
    )
endforeach