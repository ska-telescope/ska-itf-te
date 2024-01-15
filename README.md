# ska-mid-itf Readme

Welcome to the Mid ITF Tests project. Here you can find methods to connect to hosts in the Mid Integration Test Facility (ITF) network, System Under Test (SUT) and Test Equipment (TE), as well as tests (BDD and python tests) and scripts for interacting with the SUT and TE.

Control can be done using Taranta Dashboards and Jupyter Notebooks.

## Run Binderhub

Use this icon to launch a Jupyter Notebook (using Binderhub) in the ITF: [![Binder](https://k8s.miditf.internal.skao.int/binderhub/badge_logo.svg)](https://k8s.miditf.internal.skao.int/binderhub/v2/gh/ska-telescope/ska-mid-itf/HEAD)

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

## Tango info

```
$ ./mid_tango_instance_info.py -I tmc
************************************
dserver/TmCspSubarrayLeafNodeTest/tm
************************************
Commands   : AddLoggingTarget AddObjPolling DevLockStatus DevPollStatus DevRestart EventConfirmSubscription EventSubscriptionChange GetLoggingLevel GetLoggingTarget Init Kill LockDevice PolledDevice QueryClass QueryDevice QuerySubDevice QueryWizardClassProperty QueryWizardDevProperty ReLockDevices RemObjPolling RemoveLoggingTarget RestartServer SetLoggingLevel StartLogging StartPolling State Status StopLogging StopPolling UnLockDevice UpdObjPollingPeriod ZmqEventSubscriptionChange

Attributes :
        State : ON
        Status : The device is ON
The polling is ON
*************************************
dserver/TmCspSubarrayLeafNodeTest/tm2
*************************************
Commands   : AddLoggingTarget AddObjPolling DevLockStatus DevPollStatus DevRestart EventConfirmSubscription EventSubscriptionChange GetLoggingLevel GetLoggingTarget Init Kill LockDevice PolledDevice QueryClass QueryDevice QuerySubDevice QueryWizardClassProperty QueryWizardDevProperty ReLockDevices RemObjPolling RemoveLoggingTarget RestartServer SetLoggingLevel StartLogging StartPolling State Status StopLogging StopPolling UnLockDevice UpdObjPollingPeriod ZmqEventSubscriptionChange

Attributes :
        State : ON
        Status : The device is ON
The polling is ON

$ itango3
ITango 9.4.2 -- An interactive Tango client.

Running on top of Python 3.10.12, IPython 8.5 and PyTango 9.4.2

help      -> ITango's help system.
object?   -> Details about 'object'. ?object also works, ?? prints more.

IPython profile: tango

hint: Try typing: mydev = Device("<tab>

In [1]: dev = Device("dserver/TmCspSubarrayLeafNodeTest/tm")

In [2]: dev.Status()
Out[2]: 'The device is ON\nThe polling is ON'
```

## K8S stuff

Set up BITE data stream:

```
$ kubectl -n integration exec ec-bite -- python3 midcbf_bite.py --talon-bite-lstv-replay --boards=1
[midcbf_bite.py: line 52]INFO: User: root
[midcbf_bite.py: line 168]INFO: test ID: Test_1, boards_list: ['1']
[midcbf_bite.py: line 265]INFO: BITE receptors: [{'dish_id': 'SKA001', 'k': 119, 'talon': '1', 'bite_config_id': 'basic gaussian noise', 'bite_initial_timestamp_time_offset': 60.0}]
[midcbf_bite.py: line 295]INFO: Talon BITE LSTV Replay
[midcbf_bite.py: line 120]INFO: Creating dps for device server: dsgaussiannoisegen
[midcbf_bite.py: line 658]INFO: Creating device server for talondx-001/gaussiannoisegen/gn_gen_src_polX_0
[midcbf_bite.py: line 638]INFO: Created device proxy for talondx-001/gaussiannoisegen/gn_gen_src_polX_0
[midcbf_bite.py: line 658]INFO: Creating device server for talondx-001/gaussiannoisegen/gn_gen_src_polY_0
[midcbf_bite.py: line 638]INFO: Created device proxy for talondx-001/gaussiannoisegen/gn_gen_src_polY_0
[midcbf_bite.py: line 120]INFO: Creating dps for device server: dslstvbandpassfilter
[midcbf_bite.py: line 658]INFO: Creating device server for talondx-001/lstvbandpassfilter/fir_filt_src_polX_0
[midcbf_bite.py: line 638]INFO: Created device proxy for talondx-001/lstvbandpassfilter/fir_filt_src_polX_0
[midcbf_bite.py: line 658]INFO: Creating device server for talondx-001/lstvbandpassfilter/fir_filt_src_polY_0
[midcbf_bite.py: line 638]INFO: Created device proxy for talondx-001/lstvbandpassfilter/fir_filt_src_polY_0
[midcbf_bite.py: line 120]INFO: Creating dps for device server: dslstvgen
[midcbf_bite.py: line 658]INFO: Creating device server for talondx-001/lstvgen/lstv_gen
[midcbf_bite.py: line 638]INFO: Created device proxy for talondx-001/lstvgen/lstv_gen
[midcbf_bite.py: line 120]INFO: Creating dps for device server: dslstvplayback
[midcbf_bite.py: line 658]INFO: Creating device server for talondx-001/lstvplayback/lstv_pbk
[midcbf_bite.py: line 638]INFO: Created device proxy for talondx-001/lstvplayback/lstv_pbk
[midcbf_bite.py: line 120]INFO: Creating dps for device server: ska-mid-spfrx-packetizer-ds
[midcbf_bite.py: line 658]INFO: Creating device server for talondx-001/ska-mid-spfrx-packetizer/spfrx_pkt
[midcbf_bite.py: line 638]INFO: Created device proxy for talondx-001/ska-mid-spfrx-packetizer/spfrx_pkt
[midcbf_bite.py: line 120]INFO: Creating dps for device server: dslstvtonegenerator
[midcbf_bite.py: line 658]INFO: Creating device server for talondx-001/lstvtonegenerator/tone_gen_polX
[midcbf_bite.py: line 638]INFO: Created device proxy for talondx-001/lstvtonegenerator/tone_gen_polX
[midcbf_bite.py: line 658]INFO: Creating device server for talondx-001/lstvtonegenerator/tone_gen_polY
[midcbf_bite.py: line 638]INFO: Created device proxy for talondx-001/lstvtonegenerator/tone_gen_polY
[midcbf_bite.py: line 120]INFO: Creating dps for device server: dspolarizationcoupler
[midcbf_bite.py: line 658]INFO: Creating device server for talondx-001/polarizationcoupler/pol_coupler_0
[midcbf_bite.py: line 638]INFO: Created device proxy for talondx-001/polarizationcoupler/pol_coupler_0
[midcbf_bite.py: line 120]INFO: Creating dps for device server: dsvcc
[midcbf_bite.py: line 658]INFO: Creating device server for talondx-001/vcc/vcc
[midcbf_bite.py: line 638]INFO: Created device proxy for talondx-001/vcc/vcc
[midcbf_bite.py: line 120]INFO: Creating dps for device server: dscircuitswitch
[midcbf_bite.py: line 658]INFO: Creating device server for talondx-001/circuitswitch/circuit_switch
[midcbf_bite.py: line 638]INFO: Created device proxy for talondx-001/circuitswitch/circuit_switch
[midcbf_bite.py: line 120]INFO: Creating dps for device server: ska-talondx-100-gigabit-ethernet-ds
[midcbf_bite.py: line 658]INFO: Creating device server for talondx-001/ska-talondx-100-gigabit-ethernet/100g_eth_0
[midcbf_bite.py: line 638]INFO: Created device proxy for talondx-001/ska-talondx-100-gigabit-ethernet/100g_eth_0
[midcbf_bite.py: line 658]INFO: Creating device server for talondx-001/ska-talondx-100-gigabit-ethernet/100g_eth_1
[midcbf_bite.py: line 638]INFO: Created device proxy for talondx-001/ska-talondx-100-gigabit-ethernet/100g_eth_1
[midcbf_bite.py: line 120]INFO: Creating dps for device server: ska-talondx-status-ds
[midcbf_bite.py: line 658]INFO: Creating device server for talondx-001/ska-talondx-status/status
[midcbf_bite.py: line 638]INFO: Created device proxy for talondx-001/ska-talondx-status/status
[midcbf_bite.py: line 120]INFO: Creating dps for device server: dswbstatecount
[midcbf_bite.py: line 658]INFO: Creating device server for talondx-001/wbstatecount/state_count
[midcbf_bite.py: line 638]INFO: Created device proxy for talondx-001/wbstatecount/state_count
[midcbf_bite.py: line 122]INFO: Device proxies have been initialized.
[midcbf_bite.py: line 490]INFO: Entering ...
[midcbf_bite.py: line 551]ERROR: DevFailed[
DevError[
    desc = TRANSIENT CORBA system exception: TRANSIENT_CallTimedout
  origin = void Tango::Connection::connect(const string&) at (/src/cppTango/cppapi/client/devapi_base.cpp:604)
  reason = API_CorbaException
severity = ERR]

DevError[
    desc = Failed to connect to device talondx-001/lstvgen/lstv_gen
  origin = void Tango::Connection::connect(const string&) at (/src/cppTango/cppapi/client/devapi_base.cpp:604)
  reason = API_CantConnectToDevice
severity = ERR]

DevError[
    desc = Failed to read_attribute on device talondx-001/lstvgen/lstv_gen, attribute ddr4_start_addr
  origin = virtual Tango::DeviceAttribute Tango::DeviceProxy::read_attribute(const string&) at (/src/cppTango/cppapi/client/devapi_base.cpp:5589)
  reason = API_AttributeFailed
severity = ERR]
]
```

Tango console 

```
In [1]: dev = Device("talondx-001/lstvgen/lstv_gen")

In [2]: dev.Status()
AttributeError: Status
(For more detailed information type: python_error)

In [3]: dev.State()
AttributeError: State
(For more detailed information type: python_error)

In [4]: python_error
---------------------------------------------------------------------------
ConnectionFailed                          Traceback (most recent call last)
File /usr/local/lib/python3.10/dist-packages/tango/device_proxy.py:424, in __DeviceProxy__getattr(self, name)
    423 try:
--> 424     self.__refresh_cmd_cache()
    425 except Exception as e:

File /usr/local/lib/python3.10/dist-packages/tango/device_proxy.py:248, in __DeviceProxy__refresh_cmd_cache(self)
    247 def __DeviceProxy__refresh_cmd_cache(self):
--> 248     cmd_list = self.command_list_query()
    249     cmd_cache = {}

ConnectionFailed: DevFailed[
DevError[
    desc = TRANSIENT CORBA system exception: TRANSIENT_CallTimedout
  origin = void Tango::Connection::connect(const string&) at (/src/cppTango/cppapi/client/devapi_base.cpp:604)
  reason = API_CorbaException
severity = ERR]

DevError[
    desc = Failed to connect to device talondx-001/lstvgen/lstv_gen
  origin = void Tango::Connection::connect(const string&) at (/src/cppTango/cppapi/client/devapi_base.cpp:604)
  reason = API_CantConnectToDevice
severity = ERR]
]

The above exception was the direct cause of the following exception:

AttributeError                            Traceback (most recent call last)
Cell In [3], line 1
----> 1 dev.State()

File /usr/local/lib/python3.10/dist-packages/tango/device_proxy.py:452, in __DeviceProxy__getattr(self, name)
    449     if name_l in self.__get_pipe_cache():
    450         return self.read_pipe(name)
--> 452     raise AttributeError(name) from cause
    453 finally:
    454     del cause

AttributeError: State

In [5]: dev.simulationMode
AttributeError: simulationMode
(For more detailed information type: python_error)

```