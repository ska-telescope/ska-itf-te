# ska-mid-itf Readme

Welcome to the Mid ITF Tests project. Here you can find methods to connect to hosts in the Mid Integration Test Facility (ITF) network, System Under Test (SUT) and Test Equipment (TE), as well as tests (BDD and python tests) and scripts for interacting with the SUT and TE.

Control can be done using Taranta Dashboards and Jupyter Notebooks.

## Run Binderhub

Use this icon to launch a Jupyter Notebook (using Binderhub) in the ITF: [![Binder](https://10.164.0.3/binderhub/badge_logo.svg)](https://10.164.0.3/binderhub/v2/gh/ska-telescope/ska-mid-itf/HEAD)

## Makefile for SW server access

A subset of the makefile commands available in the [Deploy Mid ITF](https://gitlab.com/ska-telescope/sdi/ska-cicd-deploy-mid-itf) have been added to the resources folder.

***PRO TIP: ALWAYS ADD `--dry` TO THE END OF A MAKE COMMAND IF YOU WANT TO SEE WHAT IT IS GOING TO TRY TO DO.***

### Prerequisites

#### VPN

You need to be on the SKAO ITF VPN (connect via AnyConnect client) - see instructions in <https://confluence.skatelescope.org/display/SE/Connect+to+the+Mid+ITF+VPN>.

#### Make variables

You need to set one `make` variable in order to use your own access pattern. Do that with this command, substituting `<your-initials>` with your initials which are also the foldernames under `resources/users/`:

```
echo ME=<your-initials> >> resources/users/UserProfile.mak
```

Test if this worked, by verifying your name shows up when you ask that existential question:

```
$ make whoami
    b.lunsky
```

## Copy the KUBECONFIG file

The KUBECONFIG file enables access to the cluster resources. You'll need it to inspect deployments, or to *start an iTango session* (see below). You can get the KUBECONFIG from the CI pipeline of your deployment - follow the instructions on <https://confluence.skatelescope.org/display/SE/%5BAT-474%5D+-+Demo+how+to+continue+developing+ITF+Test+Equipment+charts>. You could also try `make copy-kubeconfig` if you feel brave.

## Run iTango

Use a Make target to run iTango:

```
make k8s-interactive
```

This normally takes a while. You can alternatively use the following instructions (slightly more advanced):

## Inspect the cluster resources

Ensure you have [k9s](https://k9scli.io/topics/install/) installed, and that remote access to the SW host is established.

You can run the `k9s` app with the correct KUBECONFIG loaded and pointing at your desired namespace, all in one go, with the `make` command:

```
make k9s
```

If the above target succeeded, you should be looking at something like this:

```
Context: minikube                                 <?> Help                                                                                               ____  __.________        
 Cluster: minikube                                                                                                                                       |    |/ _/   __   \______ 
 User:    minikube                                                                                                                                       |      < \____    /  ___/ 
 K9s Rev: v0.26.3 ⚡️v0.26.6                                                                                                                              |    |  \   /    /\___ \  
 K8s Rev: v1.24.3                                                                                                                                        |____|__ \ /____//____  > 
 CPU:     5%                                                                                                                                                     \/            \/  
 MEM:     11%                                                                                                                                                                      
┌─────────────────────────────────────────────────────────────────────────────── Contexts(all)[1] ────────────────────────────────────────────────────────────────────────────────┐
│ NAME↑                                         CLUSTER                                    AUTHINFO                                   NAMESPACE                                   │
│ minikube(*)                                   minikube                                   minikube                                   default                                     │
│                                                                                                                                                                                 │
│                                                                                                                                                                                 │
│                                                                                                                                                                                 │
│                                                                                                                                                                                 │
│                                                                                                                                                                                 │
│                                                                                                                                                                                 │
│                                                                                                                                                                                 │
│                                                                                                                                                                                 │
│                                                                                                                                                                                 │
│                                                                                                                                                                                 │
│                                                                                                                                                                                 │
│                                                                                                                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
  <contexts>                                                                                                                                                                    
```

Or, you could be looking at this:

```
Context: minikube                                 <0> all               <a>      Attach     <l>       Logs               <y> YAML                        ____  __.________        
 Cluster: minikube                                 <1> integration-itf   <ctrl-d> Delete     <p>       Logs Previous                                     |    |/ _/   __   \______ 
 User:    minikube                                 <2> default           <d>      Describe   <shift-f> Port-Forward                                      |      < \____    /  ___/ 
 K9s Rev: v0.26.3 ⚡️v0.26.6                                              <e>      Edit       <s>       Shell                                             |    |  \   /    /\___ \  
 K8s Rev: v1.24.3                                                        <?>      Help       <n>       Show Node                                         |____|__ \ /____//____  > 
 CPU:     5%                                                             <ctrl-k> Kill       <f>       Show PortForward                                          \/            \/  
 MEM:     11%                                                                                                                                                                      
┌─────────────────────────────────────────────────────────────────────────── Pods(integration-itf)[15] ───────────────────────────────────────────────────────────────────────────┐
│ NAME↑                                           PF   READY     RESTARTS STATUS         CPU   MEM   %CPU/R   %CPU/L    %MEM/R    %MEM/L IP               NODE         AGE        │
│ dashboard-ska-tango-taranta-dashboard-test-0    ●    1/1              0 Running          3    88        3        3        68        68 172.17.0.10      minikube     6h30m      │
│ mongodb-ska-tango-taranta-dashboard-test-0      ●    1/1              0 Running          3    41        1        0        16         8 172.17.0.20      minikube     6h30m      │
│ signalgenerator-smb100a-0                       ●    1/1              0 Running        101    32      202      101        65        32 172.17.0.21      minikube     6h30m      │
│ signalgenerator-test-config-5frbb               ●    0/1              0 Completed        0     0      n/a      n/a       n/a       n/a 172.17.0.11      minikube     45m        │
│ ska-tango-base-itango-console                   ●    1/1              0 Running          0     0        0        0         0         0 172.17.0.8       minikube     6h30m      │
│ ska-tango-base-tangodb-0                        ●    1/1              0 Running          1    72        1        0        28        28 172.17.0.16      minikube     6h30m      │
│ ska-tango-tangogql-0                            ●    1/1              0 Running          1    47        0        0         9         4 172.17.0.12      minikube     6h30m      │
│ spectrumanalyser-specmon26b-0                   ●    1/1              0 Running         13    31       26       13        63        31 172.17.0.18      minikube     6h30m      │
│ spectrumanalyser-test-config-whflf              ●    0/1              0 Completed        0     0      n/a      n/a       n/a       n/a 172.17.0.19      minikube     45m        │
│ tango-databaseds-0                              ●    1/1              1 Running          1     5        1        0         4         2 172.17.0.9       minikube     6h30m      │
│ tangotest-test-0                                ●    1/1              0 Running         13    41        6        2        16         8 172.17.0.17      minikube     6h30m      │
│ tangotest-test-config-276hx                     ●    0/1              0 Completed        0     0      n/a      n/a       n/a       n/a 172.17.0.13      minikube     45m        │
│ taranta-auth-ska-tango-taranta-auth-test-0      ●    2/2              0 Running          2    18        1        1         7         7 172.17.0.15      minikube     6h30m      │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
  <namespace>   <pod>
```

Learn the `k9s` commands, and open a shell (select the correct pod and use `s`) in the `ska-tango-base-itango-console` pod.
`k9s` will choose the container to open a shell in. You'll now see this:

```
<<K9s-Shell>> Pod: integration-itf/ska-tango-base-itango-console | Container: itango 
tango@ska-tango-base-itango-console:/app$ 
```

Run the `itango3` command and enjoy.

## Bash customisation

To get that nice output at the beginning of the command line, add the following to your .bashrc:

```
parse_git_branch() {
    git branch 2> /dev/null | sed -e '/^[^*]/d' -e 's/* \(.*\)/ (\1)/'
}

export PS1="\u@\h \W\[\033[32m\]\$(parse_git_branch)\[\033[00m\] $ "
```

Other customisations such as `alias`es also make life simpler. Speak to your nearest SW Support Specialist for more information.

## ITF User Access

The ansible playbooks in `resources/ansible-playbooks` are used to manage access to hosts in the Mid ITF. See `resources/ansible-playbooks/README.md` for more details.

## Talon Board

Scripts used to control the Talon boards can be found in `resources/talon`. According to the CIPA Team, switching off the Talon before tests are executed is required to perform all the BITE tests. This is because booting up the boards is the first step of the BITE test sequence.

### talon_power_lru.sh

This script is used to turn the LRU ON/OFF or to check its current status. When running the `talon_power_lru.sh` script, make sure that the `apc_pdu.expect` is in the same directory. This script also requires the following packages to be installed: `sshpass`, `expect`.

```bash
# Retrieve the LRU1 status
./talon_power_lru.sh lru1

# Turn the LRU1 ON
./talon_power_lru.sh lru1 on

# Switch the LRU1 OFF
./talon_power_lru.sh lru1 off
```

## Mid ITF test instruments

### Arbitrary Waveform Generator

FQDN: za-itf-awg.ad.skatelescope.org
IP  : 10.165.3.3
Port: 4000
Web : http://za-itf-awg.ad.skatelescope.org/Default.aspx

### Oscilloscope

FQDN: za-itf-oscilloscope.ad.skatelescope.org
IP  : 10.165.3.2
Port: 4000
Web : http://za-itf-oscilloscope.ad.skatelescope.org/

### Spectrum analyser

FQDN: za-itf-spectrum-analyser.ad.skatelescope.org
IP  : 10.165.3.4
Port: 9001

### Programmable attenuator

FQDN: za-itf-attenuator.ad.skatelescope.org
IP  : 10.165.3.6
Port: 45451

### Signal generator

FQDN: za-itf-signal-generator.ad.skatelescope.org
IP  : 10.165.3.1
Port: 5025
Web : http://za-itf-signal-generator.ad.skatelescope.org/webpages/web/html/ihp.php

## Preparing to SSH to SPFC device

Before remotely loggin in to the SPFC device using the ssh key, please add local ssh keys and
it to your ~/.ssh directory using the following steps.

Login to https://vault.skao.int/ui/ and `sign in with gitlab` button (You need to be logged in to gitlab.com
in the same browser already).
Navigate to secrets/kv/groups/ska-dev/atlas and copy the `SPFC_PRIVATE_KEY` value to a file called `spfc_rsa`
such that you have it in `~/.ssh/spfc_rsa`
Next step is to copy the `SPFC_PUBLIC_KEY` value to a file called `spfc_rsa.id` such that you have it in
`~/.ssh/spfc_rsa.id`
Next step is to add the following configuration information to your `~/.ssh/config` file:

```
Host 10.165.3.28
    KexAlgorithms +diffie-hellman-group1-sha1,diffie-hellman-group14-sha1
    IdentityFile ~/.ssh/spfc_rsa
    PubkeyAcceptedKeyTypes=+ssh-rsa
    HostKeyAlgorithms=+ssh-rsa

Host 10.165.3.33
    KexAlgorithms +diffie-hellman-group1-sha1,diffie-hellman-group14-sha1
    IdentityFile ~/.ssh/spfc_rsa
    PubkeyAcceptedKeyTypes=+ssh-rsa
    HostKeyAlgorithms=+ssh-rsa
```

The step above will enable seamless login to both SPF devices in the MID-ITF in both 
`10.165.3.28` and `10.165.3.33` IP addresses.

You should be able to login to SPFC using the generic user `skao` to SPFC.

### Register SPFC device to tango database

There is a set of commands that one can run to register the SPFC device to the tango database.
This is important, for example, in cases where registration SPFC needs to communicate with Dish.LMC

To use the SPFC registration to tango device, please ensure that the TANGO_HOST environment variable is set.
To set the TANGO_HOST variable one can simply run the `export TANGO_HOST=<ipaddress>:<port_number>` command.
Secondly please update the `resources\makefiles\spfc-register.mk` with correct SPFC configuration information.

We can extract the tango database port from the cluster under specified namespace and service name using the
following command. 
`export TANGO_HOST=$(kubectl -n ${NAMESPACE} get svc ${SERVICE_NAME} -o jsonpath={.status.loadBalancer.ingress[0].ip})`
please see `ska-mid-itf/resources/makefiles/spfc-register.mk` file with correct variable values to use as a guide.

Please note:
Before running any SPFC command please ensure that the TANGO_HOST variable is set.

Once done, you can simply run the `make register-spfc --dry-run` to preview steps that will be taken to register
the SPFC. Once satisfied with the preview, you can then `make register-spfc` to register the SPFC to tango DB.

