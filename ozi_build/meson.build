sources = ['__init__.py', 'buildapi.py', 'pep425tags.py', 'schema.py', 'vendor/pyc_wheel/src/pyc_wheel/__about__.py', 'vendor/pyc_wheel/src/pyc_wheel/__main__.py', 'vendor/pyc_wheel/src/pyc_wheel/_pyc_wheel.py']
foreach source: sources
    fs.copyfile(source)
    python.install_sources(
        source,
        pure : true,
        subdir : 'ozi_build'
    )
endforeach
