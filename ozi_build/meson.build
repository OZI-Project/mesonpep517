sources = [
    '__init__.py',
    '_pyc_wheel.py',
    '_util.py',
    'buildapi.py',
    'config.py',
    'metadata.py',
    'pep425tags.py',
    'schema.py',
]
foreach source: sources
    fs.copyfile(source)
    python.install_sources(
        source,
        pure : true,
        subdir : 'ozi_build'
    )
endforeach
