# Changelog

All notable changes to this project are documented in this file.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: [Semantic Versioning](https://semver.org/) with **infra-impact
semantics**: PATCH for in-place tweaks and docs, MINOR for new resources or
workflows, MAJOR for anything that destroys, recreates, or renames an existing
resource.

Add entries under `[Unreleased]` as you work. To release, bump `VERSION`,
rename `[Unreleased]` to `[<VERSION>] - <date>`, add an empty `[Unreleased]`
block above it, commit, then push the tag `v<VERSION>`.

`[Unreleased]` is for *changes since the last release only*.

## [Unreleased]

### Added

- `foundry-create.yml` workflow: creates the `ai` resource group through
  `azure-iac` `rg-create.yml`, then the Foundry account and project, and
  verifies both are provisioned.
- `foundry-destroy.yml` workflow: deletes the Foundry project and account,
  purges the soft-deleted account, then destroys the `ai` resource group
  through `azure-iac` `rg-destroy.yml`. Requires `confirm: Yes`.
- `release.yml` workflow: on a `v*.*.*` tag push, checks the tag against
  `VERSION` and `CHANGELOG.md`, lints, and publishes a GitHub Release.
- `VERSION` file.

### Changed

- `scripts/initvars.sh` manages the `TF_VAR_WORKLOAD` and `TF_VAR_OWNER`
  variables.

### Fixed

### Removed

- `scripts/initvars.sh` no longer manages the `TF_VAR_TARGET_PORT` variable
  or the `NVIDIA_API_KEY` secret, and deletes both from the repository.
