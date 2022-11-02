# Add SKAO Makefile includes
-include .make/base.mk

ME ?= bl ## Default user that wants to connect to the ITF machines
SSH_CONFIG_PATH ?= resources/users/$(ME)/.ssh
SSH_HOST ?= The-Beast
# add this line 
# ME = <your-three-letter-initials>
# and uncomment, in the following file:
-include ./resources/users/UserProfile.mak
-include PrivateRules.mak
-include ./resources/OpenSSHPorts.mak

USER=$(shell ssh -G $(SSH_HOST) | grep "^user " | head -1 | cut -d " " -f2-)
USER_AT=$(USER)@ # Temporarily left in - redundant

whoami:
	@echo $(USER)

####### Jump to hosts within the ITF network #######
# NOTE: you need to have EduVPN set up while       #
# SKAO IT is figuring out how to get access        #
# granted for external users into the SKAO         #
# network.                                         #
####### Any day now. ###############################

connect-jump-host: ## Connect to the Raspberry Pi
	@make jump SSH_HOST="Pi"

jump-the-beast: ## Jump to the ITF Minikube host
	@make jump SSH_HOST="The-Beast"

## TARGET: jump
## SYNOPSIS: make jump
## HOOKS: none
## VARS:
## 		SSH_CONFIG_PATH=path in this repository where .ssh/config files are
##						kept to access ITF machines. NO PRIVATE KEYS!!!
## 		SSH_HOST=hostname specified in user's .ssh/config file.
##  Force initialisation and update of all git submodules in this project.
jump: ## Jump to a host
	@ssh -F $(SSH_CONFIG_PATH)/config $(SSH_HOST)

ps-aux-ssh-tunnels: ## check if any SSH tunnels are currently open
	@ps aux | grep "ssh -N -L" | grep -v grep || echo "No SSH tunnels open at this time."

ps: ps-aux-ssh-tunnels ## alias for ps-aux-ssh-tunnels

open-tunnel:
	resources/tunnel.sh $(LOCAL_PORT) $(SOURCE_IP) $(SOURCE_PORT) $(USER)
	@ps aux | grep "ssh -N -L" | grep $(LOCAL_PORT)
	@sleep 1

close-tunnel:
	@echo "Killing PID $(PROCESS_ID)"
	@./resources/close_tunnels.sh $(LOCAL_PORT) || echo "ERROR: could not close port $(LOCAL_PORT) - PID = $(PROCESS_ID)"

### THIS IS HARDCODED AND MAY CAUSE ISSUES LATER
HAPROXY_IP := 10.20.7.7

ssh-login: close-ssh-tunnel open-ssh-tunnel
	ssh $(USER)@localhost -p 2234

open-ssh-tunnel:
	make open-tunnel LOCAL_PORT=2234 SOURCE_IP=127.0.0.1 SOURCE_PORT=22
close-ssh-tunnel:
	@make close-tunnel LOCAL_PORT=2234 PROCESS_ID=$(SSH_PORT_2234_PROCESS_ID)

K8S_PORT := 6443
open-k8s-tunnel: close-k8s-tunnel
	@make open-tunnel LOCAL_PORT=${K8S_PORT} SOURCE_IP=127.0.0.1 SOURCE_PORT=${K8S_PORT}

close-k8s-tunnel:
	@make close-tunnel LOCAL_PORT=$(K8S_PORT) PROCESS_ID=$(SSH_PORT_6443_PROCESS_ID)

copy-kubeconfig:
	scp -F $(SSH_CONFIG_PATH)/config $(SSH_HOST):/srv/deploy-itf/KUBECONFIG .
	sed -i -e "s/192\.168\.49\.2/localhost/" KUBECONFIG
	rm KUBECONFIG-e

k9s: open-k8s-tunnel launch-k9s

launch-k9s:
	k9s --kubeconfig KUBECONFIG -n integration-itf

JUPYTER_PORT := 8080
open-jupyter-tunnel: close-jupyter-tunnel
	@make open-tunnel LOCAL_PORT=${JUPYTER_PORT} SOURCE_IP=127.0.0.1 SOURCE_PORT=${JUPYTER_PORT}

close-jupyter-tunnel: ## kill the last process registered for Jupyter
	@make close-tunnel LOCAL_PORT=$(JUPYTER_PORT) PROCESS_ID=$(SSH_PORT_8080_PROCESS_ID)

TARANTA_PORT := 8000
open-taranta-tunnel: close-taranta-tunnel
	@make open-tunnel LOCAL_PORT=$(TARANTA_PORT) SOURCE_IP=127.0.0.1 SOURCE_PORT=80

close-taranta-tunnel: ## kill the last process registered for web
	@make close-tunnel LOCAL_PORT=$(TARANTA_PORT) PROCESS_ID=$(SSH_PORT_8000_PROCESS_ID)

open-all-tunnels: open-k8s-tunnel open-jupyter-tunnel open-taranta-tunnel open-ssh-tunnel
	@echo "All tunnels opened"
close-all-tunnels: close-k8s-tunnel close-jupyter-tunnel close-taranta-tunnel close-ssh-tunnel ## Close the gates!

curl-test: ## Curl to see if Taranta is accessible from command line
	@curl -s localhost:8000/integration-itf/taranta | grep Taranta
	@exit $$?

curl-test-jupyter: ## Curl to see if Jupyter is accessible from command line
	@curl -sv localhost:8080
	@exit $$?

open-jupyter: open-jupyter-tunnel curl-test-jupyter jupyter-links ## All in one target: open tunnel and check if Taranta is available

jupyter-links:
	@echo "########################################################################"
	@echo "#                                                                      #"
	@echo "# Open http://localhost:8080 in your browswer! #"
	@echo "#                                                                      #"
	@echo "########################################################################"

open-taranta: open-taranta-tunnel curl-test taranta-links ## All in one target: open tunnel and check if Taranta is available

taranta-links:
	@echo "########################################################################"
	@echo "#                                                                      #"
	@echo "# Open http://localhost:8000/integration-itf/taranta in your browswer! #"
	@echo "#                                                                      #"
	@echo "########################################################################"

