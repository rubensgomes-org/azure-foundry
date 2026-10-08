# Changelog

All notable changes to this project are documented in this file.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: [Semantic Versioning](https://semver.org/) with **infra-impact
semantics**: PATCH for in-place tweaks and docs, MINOR for new resources or
workflows, MAJOR for anything that destroys, recreates, or renames an existing
resource.

Add entries under `[Unreleased]` as you work. Do not edit the version headings
by hand: `make release-<level>` renames `[Unreleased]` to the new version and
re-seeds an empty `[Unreleased]` block above it. `make release-check` prints
the bump policy against the current `VERSION`.

`[Unreleased]` is for *changes since the last release only*.

## [Unreleased]

### Added

### Changed

### Fixed

### Removed

## [0.1.0] - 2026-10-08

### Added

- `foundry-create.yml` workflow: creates the `ai` resource group through
  `azure-iac` `rg-create.yml`, then the Foundry account and project, and
  verifies both are provisioned.
- `foundry-destroy.yml` workflow: deletes the Foundry project and account,
  purges the soft-deleted account, then destroys the `ai` resource group
  through `azure-iac` `rg-destroy.yml`. Requires `confirm: Yes`.
- `release.yml` workflow: on a `v*.*.*` tag push, checks the tag against
  `VERSION` and `CHANGELOG.md`, lints, and publishes a GitHub Release.
- `VERSION` file and a `Makefile` with the `version` and `release-*`
  targets.

### Changed

- `scripts/initvars.sh` manages the `TF_VAR_WORKLOAD` and `TF_VAR_OWNER`
  variables.
- `sonar-project.properties` scans `.github` and `scripts` instead of the
  missing `src`.
- `README.md` documents the workflows, prerequisites and configuration.

### Fixed

### Removed

- `scripts/initvars.sh` no longer manages the `TF_VAR_TARGET_PORT` variable
  or the `NVIDIA_API_KEY` secret, and deletes both from the repository.
