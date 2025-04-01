# Makefile targets for updating values.yml in Vault

VAULT_ADDR ?= https://vault.skao.int
PRODUCT_NAME ?= central-controller
VALUES_FILENAME ?= value
DATACENTRE ?= mid-aa
ENVIRONMENT ?= losberg

## TARGET: vault-login
## SYNOPSIS: target for logging on Vault
## HOOKS: none
## VARS:
##  VAULT_ADDR=[Vault server address]
##  make target for reading Vault values
vault-login: ## Get access to Vault
	@echo "Log in for Vault access"
	@echo "For the token, navigate to $(VAULT_ADDR)/ui/vault/dashboard"
	vault login -address $(VAULT_ADDR)

## TARGET: vault-status
## SYNOPSIS: target for checking Vault status
## HOOKS: none
## VARS:
##  VAULT_ADDR=[Vault server address]
##  make target for reading Vault status
vault-status: ## Check Vault status
	@echo "Check Vault status"
	@echo "Server: $(VAULT_ADDR)"
	vault status -address $(VAULT_ADDR)

## TARGET: vault-get-values
## SYNOPSIS: target for getting values from Vault
## HOOKS: none
## VARS:
##  VAULT_ADDR=[Vault server address]
##  VALUES_FILENAME=[e.g. values]
##  DATACENTRE=[Data centre e.g. mid-aa]
##  ENVIRONMENT=[Environment e.g. losberg]
##	PRODUCT_NAME=[product name e.g. central-controller]
##  make target for reading Vault values
vault-get-values: ## Get values from Vault
	@echo "Get Vault values"
	@echo "Data centre: $(DATACENTRE)"
	@echo "Environment: $(ENVIRONMENT)"
	@echo "Product: $(PRODUCT_NAME)"
	vault kv get -address $(VAULT_ADDR) -mount=$(DATACENTRE) $(ENVIRONMENT)/$(PRODUCT_NAME)

## TARGET: vault-update-values
## SYNOPSIS: target for updating values in Vault
## HOOKS: none
## VARS:
##  VAULT_ADDR=[Vault server address]
##	PRODUCT_NAME=[product name e.g. central-controller]
##  VALUES_FILENAME=[e.g. values]
##  DATACENTRE=[Data centre e.g. mid-aa]
##  ENVIRONMENT=[e.g. losberg]
##  make target for updating Vault values
vault-update-values: ## Update values in Vault
	@echo "Update Vault values"

## TARGET: vault-new-values
## SYNOPSIS: target for creating values in Vault
## HOOKS: none
## VARS:
##  VAULT_ADDR=[Vault server address]
##	PRODUCT_NAME=[product name e.g. central-controller]
##  VALUES_FILENAME=[File name e.g. value]
##  DATACENTRE=[Data centre e.g. mid-aa]
##  ENVIRONMENT=[e.g. losberg]
##  make target for creating Vault values
vault-new-values: ## Create new values in Vault
	@echo "New Vault values"

## TARGET: vault-new-version
## SYNOPSIS: target for creating a new version in Vault
## HOOKS: none
## VARS:
##  VAULT_ADDR=[Vault server address]
##	PRODUCT_NAME=[Product name e.g. central-controller]
##  VALUES_FILENAME=[File name e.g. values]
##  DATACENTRE=[Data centre e.g. mid-aa]
##  ENVIRONMENT=[e.g. losberg]
##  make target for updating Vault version
vault-new-version: ## Create new version in Vault
	@echo "Set Vault version"
