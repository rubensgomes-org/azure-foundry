# Azure CLI Commands

This file contains some az cli commands used in this project.

- get your current signed in user's object ID

```bash
az ad signed-in-user show --query id -o tsv
```

- create Terraform variable to be used for the "Foundry User"

```bash
# create the GitHub Actions variable in azure-iac
gh variable set TF_VAR_FOUNDRY_USER_OBJECT_ID --body "<object-id>"
# or for local `make apply-foundry` runs
export TF_VAR_foundry_user_object_id="<object-id>"
```

- list different cognitive service account types

```bash
az cognitiveservices account list-kinds
```

- list supported regions for current subscription

```bash
az account list-locations
```

-  list all the roles granted to the user

```bash
# USER_OBJ_ID is defined in the environment
az role assignment list \
  --assignee "${USER_OBJ_ID}" \
  --all \
  --include-inherited \
  --include-groups \
  --query "[].{role:roleDefinitionName, scope:scope}" \
  -o table
```

- grant the user access to the Foundry resource

```bash
RESOURCE_GROUP="rg-rgomesai-dev"
FOUNDRY_RESOURCE="aif-rgomesai-dev-cus"

scope="/subscriptions/${AZURE_SUBSCRIPTION_ID}"
scope+="/resourceGroups/${RESOURCE_GROUP}"
scope+="/providers/Microsoft.CognitiveServices"
scope+="/accounts/${FOUNDRY_RESOURCE}"

az role assignment create \
  --role "Foundry User" \
  --assignee-object-id "${USER_OBJ_ID}" \
  --assignee-principal-type User \
  --scope "${scope}"
```

```bash
RESOURCE_GROUP="rg-rgomesai-dev"
FOUNDRY_RESOURCE="aif-rgomesai-dev-cus"
FOUNDRY_PROJECT="proj-rgomesai-dev-cus"

scope="/subscriptions/${AZURE_SUBSCRIPTION_ID}"
scope+="/resourceGroups/${RESOURCE_GROUP}"
scope+="/providers/Microsoft.CognitiveServices"
scope+="/accounts/${FOUNDRY_RESOURCE}/projects/${FOUNDRY_PROJECT}"

# Show the roles assigned at the project.
az role assignment list \
  --assignee-object-id "${USER_OBJ_ID}" \
  --scope "${scope}" \
  --query "[].roleDefinitionName" -o tsv

# delete the old role
az role assignment delete \
  --assignee "${USER_OBJ_ID}" \
  --role "Cognitive Services OpenAI User" \
  --scope "${scope}"
```