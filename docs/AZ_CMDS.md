# Azure CLI Commands

This file contains some az cli commands used in this project.

## 

- list different cognitive service account types

```bash
az cognitiveservices account list-kinds
```

- list supported regions for current subscription

```bash
az account list-locations
```

- grant the user access to the Foundry project

```bash
scope="/subscriptions/${AZURE_SUBSCRIPTION_ID}"
scope+="/resourceGroups/${RESOURCE_GROUP}"
scope+="/providers/Microsoft.CognitiveServices"
scope+="/accounts/${FOUNDRY_RESOURCE}/projects/${FOUNDRY_PROJECT}"

az role assignment create \
  --role "Cognitive Services OpenAI User" \
  --assignee-object-id "${USER_OBJ_ID}" \
  --assignee-principal-type User \
  --scope "${scope}"
```