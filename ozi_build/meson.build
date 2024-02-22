sources = ['__init__.py', 'buildapi.py', 'pep425tags.py', 'schema.py']
python.install_sources(
    sources,
    pure : true,
    subdir : 'ozi_build'
)
foreach source: sources
    fs.copyfile(source)
endforeach
