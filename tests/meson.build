# OZI 0.16.0 meson.build:test_files,test_children
# Part of OZI.build.
# See LICENSE.txt in the project root for details.
# DO NOT EDIT BY HAND - This file was generated for use with OZI tools.
# ozi-fix -> meson rewrite is the standard editing pipeline.
test_files = ['ozi.phony']
foreach file: test_files
    if file != 'ozi.phony'
        fs.copyfile(file)
        if not meson.is_subproject() or get_option('install-subprojects').enabled()
            python.install_sources(file, subdir: 'ozi_build' / 'tests')
        endif
    endif
endforeach
test_children = ['ozi.phony']
foreach child: test_children
    if child != 'ozi.phony'
        subdir(child)
    endif
endforeach
if false
    executable('test_files', test_files)
    executable('test_children', test_children)
endif