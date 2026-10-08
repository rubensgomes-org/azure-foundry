# Azure Foundry

[![OpenAI](https://img.shields.io/badge/OpenAI-3.22%2B-8250df?logo=openai)](https://github.com/openai/openai-python)
[![GitHub](https://img.shields.io/badge/GitHub-Actions-0969da?logo=github+actions)](https://github.com/features/actions)
[![Microsoft](https://img.shields.io/badge/Microsoft-Azure-0969da)](https://azure.microsoft.com/en-us)
[![AI](https://img.shields.io/badge/AI-Assisted-d29922?logo=claude+code)](https://github.com/rubensgomes-org/azure-foundry/blob/main/AI_DISCLAIMER.md)
[![license](https://img.shields.io/badge/license-MIT-1a7f37)](https://github.com/rubensgomes-org/azure-foundry/blob/main/LICENSE)

---

## Features

GitHub Actions workflows (`.github/workflows`):

- `foundry-create`: creates the `ai` resource group (via `azure-iac`
  `rg-create`), an Azure AI Foundry account and a project, then verifies
  they are provisioned.
- `foundry-destroy`: deletes the project and account, purges the
  soft-deleted account, then destroys the `ai` resource group (via
  `azure-iac` `rg-destroy`).
- `release`: publishes a GitHub Release when a `v*.*.*` tag matching
  `VERSION` and `CHANGELOG.md` is pushed.

## AI Disclaimer

This project includes code and documentation created with the assistance of AI
tools. For details on usage, limits, and review practices, please see the
[AI Disclaimer](https://github.com/rubensgomes-org/azure-foundry/blob/main/AI_DISCLAIMER.md).

## Prerequisites

- An Azure service principal with rights to the target subscription.
- The `azure-iac` Terraform state backend already bootstrapped.
- GitHub CLI (`gh`) and bash 4.2+ to run `scripts/initvars.sh`.

## Installation

Run the `foundry-create` workflow, choosing the environment (`dev` or `lab`).
Names default to `rg-<workload>ai-<env>`, `aif-<workload>-<env>` (account and
custom domain) and `proj-<workload>-<env>`. The account and project names can
be overridden; the account name must be globally unique.

## Uninstall

Run the `foundry-destroy` workflow with the same environment and names, and
`confirm` set to `Yes`.

## Configuration

Export the values below, then run `scripts/initvars.sh` to set the
repository's Actions variables and secrets:

- `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID`,
  `AZURE_SUBSCRIPTION_ID` (or the `ARM_*` equivalents).
- `TF_VAR_workload`, `TF_VAR_owner`, `TF_VAR_location`.
- `TF_VAR_backend_resource_group_name`, `TF_VAR_storage_account_id`,
  `TF_VAR_container_name` (the `azure-iac` state backend).
- `PYPI_API_TOKEN`, `SONAR_TOKEN`.

## Open Source Project Information

This project is open source and publicly hosted on GitHub at
[rubensgomes-org](https://github.com/rubensgomes-org/). It is
published under an
[OSI-approved open-source license](https://opensource.org/licenses).

> [!IMPORTANT]
> Public availability and the use of an OSI-approved license are requirements 
> for eligibility to
> use [SonarQube Cloud](https://sonarcloud.io/) under its free plan for
> open-source projects.

## License

The project is licensed under the
[MIT License](https://github.com/rubensgomes-org/azure-foundry/blob/main/LICENSE).

## Links

- [GitHub Project](https://github.com/rubensgomes-org/azure-foundry)

---
Author: [Rubens Gomes](https://rubensgomes.com/)
