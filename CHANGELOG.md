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

## [0.0.9] - 2026-10-13

### Added

### Changed

- `aif-create.yml` and `aif-destroy.yml` call the `azure-iac` reusable
  `aif-create.yml` / `aif-destroy.yml@v0` workflows, which manage the
  Foundry resource and project with Terraform. The `project_name` input is
  removed.

### Fixed

### Removed

- The `USER_OBJ_ID` Actions variable and the `aif-create` "Foundry User"
  grant; `scripts/initvars.sh` deletes the variable as retired.

## [0.0.8] - 2026-10-13

### Added

### Changed

- Renamed the `foundry-create`, `foundry-destroy`, `foundry-model-deploy`
  and `foundry-model-delete` workflows to `aif-create`, `aif-destroy`,
  `aif-model-deploy` and `aif-model-delete`.

### Fixed

### Removed

## [0.0.7] - 2026-10-13

### Added

- `foundry-model-deploy.yml` deploys a model on the Foundry resource
  (default `gpt-5-nano` `2025-08-07`, `OpenAI`, `GlobalStandard`).
- `foundry-model-delete.yml` deletes a model deployment.

### Changed

### Fixed

### Removed

## [0.0.6] - 2026-10-08

### Added

### Changed

- `foundry-create.yml` grants "Foundry User" on the Foundry resource
  instead of the project. Existing project-scope role assignments are not
  removed; delete them with `az role assignment delete`.
- `docs/AZ_CMDS.md` grant example uses "Foundry User" at resource scope.

### Fixed

- `foundry-create.yml` failed with "Role 'Azure AI User' doesn't exist";
  it now grants "Foundry User" by role ID.

### Removed

## [0.0.5] - 2026-10-08

### Added

### Changed

- `foundry-create.yml` grants the "Azure AI User" role instead of
  "Cognitive Services OpenAI User".

### Fixed

### Removed

## [0.0.4] - 2026-10-08

### Added

### Changed

### Fixed

### Removed

- `foundry_resource` workflow input; the name is always
  `aif-<workload>-<env>`.

## [0.0.3] - 2026-10-08

### Added

### Changed

### Fixed

### Removed

- `foundry-destroy.yml` no longer destroys the `ai` resource group
  (`azure-iac` `rg-destroy.yml` call removed).

## [0.0.2] - 2026-10-08

### Added

- `foundry-create.yml` grants the `USER_OBJ_ID` user the "Cognitive Services
  OpenAI User" role on the Foundry project.
- `scripts/initvars.sh` manages the `USER_OBJ_ID` variable.
- `docs/AZ_CMDS.md` lists useful `az` commands.

### Changed

- `foundry-create.yml` and `foundry-destroy.yml`: the `account_name` input is
  renamed `foundry_resource`.
- `foundry-create.yml` and `foundry-destroy.yml` create and purge the Foundry
  resource and project in `centralus` instead of `TF_VAR_LOCATION`.
- `foundry-create.yml` sets the Foundry resource SKU from a `SKU` constant
  (`S0`).
- `foundry-create.yml` and `foundry-destroy.yml` say "Foundry resource"
  instead of "Foundry account" in step names, inputs and log messages.

### Fixed

### Removed

## [0.0.1] - 2026-10-08

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
