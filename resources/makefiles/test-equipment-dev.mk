# These variables should be set in order to deploy release candidates of
# the Test Equipment charts published to the Gitlab registry from the Test
# Equipment repository - registry.gitlab.com/ska-telescope/ska-ser-test-equipment

ifeq ($(CI_JOB_NAME),deploy-test-equipment-for-verification) # if CI_JOB_NAME is deploy-test-equipment
# # Set K8S_EXTRA_PARAMS for deploying Test Equipment during development of the Test Equipment charts
TE_REGISTRY ?= registry.gitlab.com/ska-telescope/ska-ser-test-equipment
TE_IMAGE ?= ska-ser-test-equipment
COMMIT_HASH ?= dde108e2
#TE_VERSION ?= 0.8.3 # this line can be commented out or overwritten by the following line
TE_VERSION ?= 0.8.3-dev.c$(COMMIT_HASH) # This is the version of the image that we want to pull from https://gitlab.com/ska-telescope/ska-ser-test-equipment/container_registry/3213235

K8S_EXTRA_PARAMS = \
			--set test-equipment.image.registry=$(TE_REGISTRY) \
			--set test-equipment.image.image=$(TE_IMAGE) \
			--set test-equipment.image.tag=$(TE_VERSION) \
			--set test-equipment.image.pullPolicy=Always
endif

itf-lmc-stage:
	helm upgrade --install dev charts/dish-lmc -n $(KUBE_NAMESPACE) \
		--set "global.dishes={001}" \
		--set "global.minikube=true" \
		--set "dishlmc.ska-mid-dish-manager.ska-mid-dish-simulators.enabled=true" \
		--set "dishlmc.ska-mid-dish-manager.ska-mid-dish-simulators.deviceServers.spfrxdevice.enabled=true" \
		--set "dishlmc.ska-mid-dish-manager.ska-mid-dish-simulators.deviceServers.spfdevice.enabled=true" \
		--set "dishlmc.ska-mid-dish-manager.ska-mid-dish-simulators.ska-tango-base.enabled=false" \
		--set "dishlmc.ska-mid-dish-ds-manager.ska-mid-dish-simulators.enabled=false" \
		--set "dishlmc.ska-mid-dish-ds-manager.ska-tango-base.enabled=false"
