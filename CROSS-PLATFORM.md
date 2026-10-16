# Platform support

See [installation instructions](docs/INSTALL.md) and [native builds](docs/BUILD.md).

The same Python/PySide6/Qt source supports Windows, macOS and Linux through host
paths, engine asset selection and native process/folder handling. The Windows
desktop app and real download examples were tested locally. Native CI build and
startup checks do not establish that every desktop/environment works; macOS/Linux
interactive download behavior still needs community testing.

The redesigned Qt view requires macOS 14+. Keep `_internal` beside the executable on Windows/Linux. Current native build results are linked from Actions; interactive macOS/Linux download behavior remains unverified.
