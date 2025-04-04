# Makefile targets for controlling flux

GIT_REPO ?= ska-mid-itf
GIT_BRANCH ?= ""
K8S_NAMESPACE ?= ska-mid-helmreleases
KUSTOM_NAME ?= foo

ifeq ($(GIT_BRANCH), "")
GIT_BRANCH := $(shell git branch | grep ^\* | cut -c3-)
endif

## TARGET: flux-suspend
## SYNOPSIS: target for suspending resources
## HOOKS: none
## VARS:
##  GIT_REPO=[Git repository name]
##  K8S_NAMESPACE=[Kubernetes namespace]
##  make target for suspending resources
flux-suspend: ## Suspend resources
	@echo "Suspend flux resources for git repository $(GIT_REPO) and namespace $(K8S_NAMESPACE)"
	flux suspend source git $(GIT_REPO) -n $(K8S_NAMESPACE)

## TARGET: flux-resume
## SYNOPSIS: target for resuming suspended resources
## HOOKS: none
## VARS:
##  GIT_REPO=[Git repository name]
##  K8S_NAMESPACE=[Kubernetes namespace]
##  make target for resuming suspended resources
flux-resume: ## Resume suspended resources
	@echo "Resume flux resources for git repository $(GIT_REPO) and namespace $(K8S_NAMESPACE)"
	flux resume source git $(GIT_REPO) -n $(K8S_NAMESPACE)

## TARGET: flux-suspend-kustomization
## SYNOPSIS: target for suspending kustomization
## HOOKS: none
## VARS:
##  KUSTOM_NAME=[kustomization name]
##  make target for suspending kustomization
flux-suspend-kustomization: ## Suspend kustomization
	@echo "Suspend flux kustomization $(KUSTOM_NAME)"
	flux suspend kustomization $(KUSTOM_NAME)

## TARGET: flux-resume-kustomization
## SYNOPSIS: target for resuming suspended kustomization
## HOOKS: none
## VARS:
##  KUSTOM_NAME=[kustomization name]
##  make target for resuming suspended kustomization
flux-resume-kustomization: ## Resume suspended kustomization
	@echo "Resume flux kustomization $(KUSTOM_NAME)"
	flux resume kustomization $(KUSTOM_NAME)

## TARGET: flux-delete-kustomization
## SYNOPSIS: target for deleting suspended kustomization
## HOOKS: none
## VARS:
##  KUSTOM_NAME=[kustomization name]
##  make target for deleting suspended kustomization
flux-delete-kustomization: ## Delete kustomization
	@echo "Resume flux kustomization $(KUSTOM_NAME)"
	flux delete kustomization $(KUSTOM_NAME)

## TARGET: get-current-branch
## SYNOPSIS: target for getting current git branch
## HOOKS: none
## VARS:
##  GIT_REPO=[Git repository name]
##  make target for getting current git branch
get-current-branch: ## get current git branch
	@echo $(GIT_BRANCH)

## TARGET: set-current-branch
## SYNOPSIS: target for setting current git branch
## HOOKS: none
## VARS:
##  GIT_BRANCH=[Git branch name]
##  make target for setting current git branch
set-current-branch: ## set current git branch
	@git checkout $(GIT_BRANCH)
