# Azure Foundry

[![OpenAI](https://img.shields.io/badge/OpenAI-3.22%2B-8250df?logo=openai)](https://github.com/openai/openai-python)
[![GitHub](https://img.shields.io/badge/GitHub-Actions-0969da?logo=github+actions)](https://github.com/features/actions)
[![Microsoft](https://img.shields.io/badge/Microsoft-Azure-0969da)](https://azure.microsoft.com/en-us)
[![AI](https://img.shields.io/badge/AI-Assisted-d29922?logo=claude+code)](https://github.com/rubensgomes-org/azure-foundry/blob/main/AI_DISCLAIMER.md)
[![license](https://img.shields.io/badge/license-MIT-1a7f37)](https://github.com/rubensgomes-org/azure-foundry/blob/main/LICENSE)

---

## Features

GitHub Actions workflows (`.github/workflows`):

- `aif-create`: creates the `ai` resource group, an Azure AI Foundry
  account and a project with the `azure-iac` Terraform `aif-create`
  workflow.
- `aif-destroy`: deletes the project and account, then purges the
  soft-deleted account, with the `azure-iac` `aif-destroy` workflow.
- `aif-model-deploy`: deploys a model (default `gpt-5-nano`,
  `GlobalStandard`) on the Foundry account.
- `aif-model-delete`: deletes a model deployment.
- `foundry-create-all`: creates the Container Apps, their dependencies and
  the Foundry account and project with the `azure-iac` workflow of the
  same name.
- `foundry-destroy-all`: destroys everything `foundry-create-all` creates,
  with the `azure-iac` workflow of the same name.
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

Run the `aif-create` workflow, choosing the environment (`dev` or `lab`)
and, optionally, a region (empty uses `TF_VAR_foundry_location`).
It creates `rg-<workload>ai-<env>`, `aif-<workload>-<env>` (account and
custom domain) and `proj-<workload>-<env>`. Select `yes` for
`app_insights` to also create `appi-<workload>ai-<env>` for agent tracing;
`no` deletes an existing one. To also create the Container
Apps, run `foundry-create-all` instead, passing the `apps` JSON array.

Then run the `aif-model-deploy` workflow to deploy a model. The deployment
name defaults to the model name.

## Uninstall

To remove only a model, run the `aif-model-delete` workflow with the
deployment name and `confirm` set to `Yes`.

Run the `aif-destroy` workflow with the same environment and `confirm` set
to `Yes`. If the estate was created by `foundry-create-all`, run
`foundry-destroy-all` instead.

## Configuration

Export the values below, then run `scripts/initvars.sh` to set the
repository's Actions variables and secrets:

- `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID`,
  `AZURE_SUBSCRIPTION_ID` (or the `ARM_*` equivalents).
- `TF_VAR_workload`, `TF_VAR_owner`, `TF_VAR_location`,
  `TF_VAR_foundry_location` (optional, defaults to `TF_VAR_location`).
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
