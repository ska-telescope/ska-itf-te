## TARGET: vault-get-values
## SYNOPSIS: target for updating values.yml in Vault
## HOOKS: none
## VARS:
##	PRODUCT_NAME=[product name e.g. central-controller]
##  VALUES_FILENAME=[e.g. value]
##  DATACENTRE=[e.g. mid-aa]
##   ENVIRONMENT=[e.g. losberg]
##  make target for reading and updating Vault values
vault-get-values:
	@echo "Get Vault values"

vault-update-values:
	@echo "Update Vault values"

vault-new-values:
	@echo "New Vault values"

vault-new-version:
	@echo "Get Vault version"
