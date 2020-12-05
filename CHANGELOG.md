# Changelog

All notable changes to this project are documented in this file.

## [Unreleased]

### Added

- n/a

### Changed

- n/a

### Fixed

- n/a

## [0.3.2] - 2020-12-05

### Changed

- Start CherryPy in environment "staging"

### Fixed

- Traceback when on_change_command is not set

## [0.3.1] - 2020-12-05

### Added

- Ask for listening interface and port in setup assistant

### Changed

- Strip quotes from on_change_command

## [0.3.0] - 2020-12-05

### Added

- Execute a user-defined command on config changes
- Drop root privileges after binding to listening port
- Allow specifying bind interface and listening port in config file

### Fixed

- Update QR code also on description change
- Create QR code image directory (/var/lib/wgfrontend) with correct permissions

## [0.2.2] - 2020-12-02

### Fixed

- Also add webroot and templates in PyPi package

## [0.2.1] - 2020-12-02

### Changed

- Improve button naming when adding new client

### Fixed

- PyPi packaging

## [0.2.0] - 2020-11-26

### Added

- CSS stylesheet for nicer appearance

### Changed

- Improved user guidance

### Fixed

- Release with activated session handling

## [0.1.0] - 2020-11-19

### Added

- First public release to Github.
