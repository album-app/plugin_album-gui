# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

We use the following:

- `Added` for new features.
- `Changed` for changes in existing functionality.
- `Deprecated` for soon-to-be removed features.
- `Removed` for now removed features.
- `Fixed` for any bug fixes.
- `Security` in case of vulnerabilities.

## [unreleased]

### Fixed

- The run form of a solution could not be opened when a `file` or `directory` argument had a default value
  (`FileWidget.set_value` did not accept a value), the "set to default" button failed the same way.
  `string` arguments with a non-string default failed as well.
- `integer` and `float` arguments can now be negative and larger than 1000000 / 999999. The spin boxes started at 0,
  so negative values could not be entered and negative defaults were silently replaced by 0.
- Default values `0`, `0.0`, `False` and `""` are now applied (and offered by "set to default") instead of being
  treated as if the argument had no default.
- The run form only passes the arguments whose value was changed. Unchanged defaults are applied by the solution
  itself, with their declared type and precision: before, an argument without type and the default `False` received
  the truthy string `"0"`, and a `float` default like `1e-07` was rounded to `0.0` by the spin box.
- A default value that a widget cannot show (e.g. `""` for an `integer` or `float` argument, or an integer outside
  -2147483648..2147483647) no longer breaks the run form; the argument is shown as unset and a warning is logged.
- Argument values are passed as `--name=value`, so values starting with `-` that are not plain negative numbers
  (e.g. `-1e-05` for small negative floats, or a text like `-v`) are no longer taken for options by the solution's
  argument parser (argparse of Python 3.12 and older rejected them).

## [0.5.1]

### Changed

- pyproject.toml over setup.cfg
- Changelog to repository 

[unreleased]: https://gitlab.com/album-app/album-gui/-/compare/v0.5.1...HEAD
[0.5.1]: https://gitlab.com/album-app/album-gui/-/compare/v0.5.0...v0.5.1
[0.5.0]: https://gitlab.com/album-app/album-gui/-/compare/v0.4.5...v0.5.0
[0.4.5]: https://gitlab.com/album-app/album-gui/-/compare/v0.4.4...v0.4.5
[0.4.4]: https://gitlab.com/album-app/album-gui/-/compare/v0.4.3...v0.4.4
[0.4.3]: https://gitlab.com/album-app/album-gui/-/compare/v0.4.2...v0.4.3
[0.4.2]: https://gitlab.com/album-app/album-gui/-/compare/v0.4.1...v0.4.2
[0.4.1]: https://gitlab.com/album-app/album-gui/-/compare/v0.4.0...v0.4.1
[0.4.0]: https://gitlab.com/album-app/album-gui/-/compare/v0.3.0...v0.4.0
[0.3.0]: https://gitlab.com/album-app/album-gui/-/compare/v0.2.1...v0.3.0
[0.2.1]: https://gitlab.com/album-app/album-gui/-/compare/v0.1.0...v0.2.1
[0.1.0]: https://gitlab.com/album-app/album-gui/-/tags/v0.1.0
