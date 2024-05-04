sources = ['__init__.py', 'buildapi.py', 'pep425tags.py', 'schema.py', '_pyc_wheel.py']
foreach source: sources
    fs.copyfile(source)
    python.install_sources(
        source,
        pure : true,
        subdir : 'ozi_build'
    )
endforeach
