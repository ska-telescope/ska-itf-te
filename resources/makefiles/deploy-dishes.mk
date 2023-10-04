## TARGET: deploy-multi-dishes
## SYNOPSIS: make deploy-multi-dishes
## HOOKS: none
## VARS: DISH_IDS
##  make target for deployment of multiple instances of DishLMC

deploy-multi-dishes:
	@echo "Running installation for dish IDs $(DISH_IDS)";
	@for dish in $(DISH_IDS); do \
		make dish-vars KUBE_NAMESPACE=dish-lmc-$$dish; \
	done;

dish-vars:
	$(info KUBE_NAMESPACE: $(KUBE_NAMESPACE))
