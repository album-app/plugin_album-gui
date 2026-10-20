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

## [0.5.2]

### Changed

- "Update Album" with another album-package branch than `main` (the developer option of the dialog) downloads the
  installer of the `<name>_installer_build_test` jobs. album-package keeps only main's installers, the ones of other
  branches are built by these jobs and expire after a day.
- Python 3.14 is listed among the supported Python versions; the CI tests it
- requires album 1.0 (`album>=1.0.0,<2.0.0`, was `album>=0.12,<0.13`)

### Fixed

- The run form of a solution could not be opened when a `file` or `directory` argument had a default value
  (`FileWidget.set_value` did not accept a value), the "set to default" button failed the same way.
  `string` arguments with a non-string default failed as well.
- `integer` and `float` arguments can now be negative and larger than 1000000 / 999999. The spin boxes started at 0,
  so negative values could not be entered and negative defaults were silently replaced by 0.
- Default values `0`, `0.0`, `False` and `""` are now applied (and offered by "set to default") instead of being
  treated as if the argument had no default.
- The run form takes the arguments as the installed solution declares them, not from its catalog entry (album#240).
  The catalog entry has no default `None`, so the form asked for a value of such an argument, which the solution takes
  as optional; it had no `0`, `False` or `""` either where the catalog held the same argument without a default, and
  the `required` of another solution with the same argument. If the installed solution cannot be read, the form shows
  the arguments of the catalog entry, with a warning.
- The run form only passes the arguments whose value was changed. Unchanged defaults are applied by the solution
  itself, with their declared type and precision: before, an argument without type and the default `False` received
  the truthy string `"0"`, and a `float` default like `1e-07` was rounded to `0.0` by the spin box.
- A default value that a widget cannot show (e.g. `""` for an `integer` or `float` argument, or an integer outside
  -2147483648..2147483647) no longer breaks the run form; the argument is shown as unset and a warning is logged.
- Argument values are passed as `--name=value`, so values starting with `-` that are not plain negative numbers
  (e.g. `-1e-05` for small negative floats, or a text like `-v`) are no longer taken for options by the solution's
  argument parser (argparse of Python 3.12 and older rejected them).
- `album add-shortcut <solution>` ignored the solution and always created the generic "Album" shortcut. It now creates
  an "Album - <solution>" shortcut (with its own launcher script on Windows) that runs `album gui <solution>`.
  Relative solution paths are made absolute. `album add-shortcut` without a solution is unchanged.
- Shortcuts did not start when the home directory contained spaces: the micromamba executable in the Windows `.bat`
  file and the `.bat` file in the shortcut were not quoted. Paths are now quoted in the Windows, macOS and Linux
  launchers (`%` and `&` in Windows paths are handled as well).
- The "Update Album" dialog on macOS tried to download the installer from the `macos_installer_build` job, which
  album-package replaced by one job per architecture. It now downloads the installer of the machine's architecture
  (`macos_installer_build_arm64` or `macos_installer_build_x86_64`). On unsupported systems it shows a message instead
  of requesting an invalid URL.
- "Update Now" in the "Update Album" dialog closed Album without starting the downloaded installer on Windows and
  macOS: the command passed to `cmd.exe` and to Terminal (via `osascript`) was wrapped in literal double quotes, which
  cmd reports as "not recognized" and which is an AppleScript syntax error. The installer path is now quoted for each
  platform (also for the Linux terminal), and an error is logged if no terminal can be opened.
- The name of a per-solution shortcut created from a URL no longer contains the query or fragment of the URL
  (e.g. `?inline=false`).
- A progress bar of a solution, such as one of tqdm, became a line in the log of the running solution for every
  update (album#217). With album-environments that marks these updates (album-environments!33), the log shows the
  first state of the bar, one state every 30 seconds and its final state.

## [0.5.1]

### Changed

- pyproject.toml over setup.cfg
- Changelog to repository 

[unreleased]: https://gitlab.com/album-app/album-gui/-/compare/v0.5.2...HEAD
[0.5.2]: https://gitlab.com/album-app/album-gui/-/compare/v0.5.1...v0.5.2
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
