# These variables should be set in order to deploy release candidates of
# the Test Equipment charts published to the Gitlab registry from the Test
# Equipment repository - registry.gitlab.com/ska-telescope/ska-ser-test-equipment

ifeq ($(CI_JOB_NAME),deploy-test-equipment-for-verification) # if CI_JOB_NAME is deploy-test-equipment
# # Set K8S_EXTRA_PARAMS for deploying Test Equipment during development of the Test Equipment charts
TE_REGISTRY ?= registry.gitlab.com/ska-telescope/ska-ser-test-equipment
TE_IMAGE ?= ska-ser-test-equipment
TE_VERSION ?= 0.7.4-dev.c92d86ef7 # This should be dynamically inherited and used only when the upstream changes

K8S_EXTRA_PARAMS = \
			--set test-equipment.image.registry=$(TE_REGISTRY) \
			--set test-equipment.image.image=$(TE_IMAGE) \
			--set test-equipment.image.tag=$(TE_VERSION) \
			--set test-equipment.image.pullPolicy=Always
endif