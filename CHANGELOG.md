# Changelog

All notable changes to this project are documented in this file.

## [Unreleased]

### Added

- n/a

### Changed

- n/a

### Fixed

- Use UNIX line endings in wrapper file

## [0.9.2] - 2021-11-20

### Fixed

- Fix and clean systemd service script

## [0.9.1] - 2021-11-02

### Fixed

- Fix file extension in /etc/sysctl.d so that file is not getting ignored

## [0.9.0] - 2021-09-24

### Added

- Explain ip addresses for ProxyARP using addresses out of local network
- Default value for WireGuard interface ip address out of local network

## [0.8.0]

### Added

- Automatically configure ip forwarding if requested by user

## [0.7.0] - 2021-03-05

### Added

- Added systemd service configuration for wgfrontend

### Changed

- Improve logging for on_change_command execution
- Change indentation and strip quotes in more controlled manner

## [0.6.0] - 2021-02-26

### Added

- Add option to install suduers config for default on_change_command

## [0.5.0] - 2021-02-18

### Added

- Reworked setup assistant

### Changed

- Added some explanatory text

### Fixed

- Fixed extra brackets

## [0.4.0] - 2021-01-26

### Added

- Provide more information and automation, e.g. ProxyARP setup

### Fixed

- Remove debug print statement

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
