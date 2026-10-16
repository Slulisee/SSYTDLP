# Qt for Python runtime

This redesigned UI uses PySide6-Essentials 6.12.0 and shiboken6 6.12.0.
SSYTDLP's own source retains its MIT license. Qt/PySide retain their own licenses.
The PyPI distributions offer open-source LGPLv3/GPL alternatives; commercial
license text included in those distributions is preserved as an upstream notice.

The folder build dynamically loads Qt DLLs from `_internal/PySide6`. Keep this
folder replaceable. Application source, dependency pins and build scripts are
included so the app can be rebuilt with a compatible Qt/PySide installation.

- [Qt for Python licenses](https://doc.qt.io/qtforpython-6/licenses.html)
- [PySide6-Essentials distribution](https://pypi.org/project/PySide6-Essentials/6.12.0/)
- [PySide/Shiboken source, v6.12.0](https://code.qt.io/pyside/pyside-setup.git/tree/?h=v6.12.0)
- [Qt Base source, v6.12.0](https://code.qt.io/qt/qtbase.git/tree/?h=v6.12.0)
- [Qt SVG source, v6.12.0](https://code.qt.io/qt/qtsvg.git/tree/?h=v6.12.0)

LGPLv3 and GPLv3 texts are supplied beside this notice, along with the installed
distribution notices. Downloaded media has its own rights, separate from the UI.
