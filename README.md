# ska-itf-te

## Documentation
For more information on this project please see the [`project documentation`](https://developer.skao.int/projects/ska-telescope-ska-mid-itf/en/latest/) in the Developer Portal.

## Makefile for SW server access
A subset of the makefile commands available in the [Deploy Mid ITF](https://gitlab.com/ska-telescope/sdi/ska-cicd-deploy-low-itf) have been added to the resources folder.

#### PRO TIP: ALWAYS ADD ` --dry` TO THE END OF A MAKE COMMAND IF YOU WANT TO SEE WHAT IT IS GOING TO TRY TO DO.

### Prerequisites

#### VPN
You need to be on the SARAO VPN (or in the SARAO network) in order for this to work.
#### Make variables
You need to set one `make` variable in order to use your own acces pattern. Do that with this command, substituting `<your-initials>` with your initials which are also the foldernames under `resources/users/`:
```
$ echo ME=<your-initials> >> resources/users/UserProfile.mak
```
Test if this worked, by verifying your name shows up when you ask that existential question:
```
$ make whoami
    b.lunsky
```
#### Set up passwordless SSH access

First SSH onto the machine, using your Jira/Confluence password when asked for it:
```
$ make ssh-login
make open-tunnel LOCAL_PORT=2234 SOURCE_IP=10.20.7.7 SOURCE_PORT=22
make[1]: Entering directory '/Users/aragorn/code/ska-itf-te'
aragorn          96903   0.0  0.0 33600116   1144 s004  S+    3:13pm   0:00.00 /bin/sh -c ps aux | grep "ssh -N -L" | grep 2234
aragorn          96900   0.0  0.0 33762352   2480 s004  S+    3:13pm   0:00.01 ssh -N -L 2234:10.20.7.7:22 pi@mid-itf.duckdns.org -p 2322
ssh b.lunsky@localhost -p 2234
b.lunsky@localhost's password:
```
Now create a folder called `.ssh` and exit:
```
b.lunsky@za-itf-sw:~ $ mkdir ~/.ssh
b.lunsky@za-itf-sw:~ $ exit
logout
Connection to localhost closed.
<your-own-machine> $ 
```

Jump to The Beast using the `make jump` command. You'll be asked your password - this is the same one you use for logging into JIRA.
```
$ make jump
The authenticity of host 'za-itf-sw.ad.skatelescope.org (10.20.7.7)' can't be established.
ED25519 key fingerprint is SHA256:fPLTftusFxQs0pdLR9bORpXvHedro2bEX/NtbEEWrkA.
This key is not known by any other names
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
Warning: Permanently added 'za-itf-sw.ad.skatelescope.org' (ED25519) to the list of known hosts.
password:_ 
```
Once you've logged in successfully, create a `.ssh` directory if it doesn't exist yet, and add a file that should contain your public key. You can do all of this by executing the following command just after logging in (again, replace `<your-initials>` with your initials):
```
$ mkdir .ssh || true && cp /srv/deploy-itf/resources/users/<your-initials>/id_rsa.pub .ssh/authorized_keys
```
Confirm that this worked:
```
$ cat .ssh/authorized_keys
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCbVN/rskAjcps8H/gp2zuJ+Ha8NK/8ColFxx8dyTftbNN6eljffUqKCbm6J3oZpQTcvgw0gX0sk0CaeQgRODX4DfzBqWC3zV9m7LfrTYfF71oGjcj5WI5c7/KCtCw8JCADwsUJhoYwWMQWTyCGd+kf+1Clz4kcqGwdDHVI1KAtU6kxXLXTe8HC42YdHf5BhhWFei9fvWRopjPVm2wmjuKLm1RWAM4Llh4dEyQmLONK3QeflRPGAOMLQwBAf3JxQ5FFpGjfrpW2D/9CJXD/vDuTbOyVFjINzoX677bJTFx0vJZrezCWVnLUW9PzYqO9wS3F984fzM9lG7ZYyHUklqIlZ8T4iHhfnCQU2r533wecno6fb1ePC2VqE2dipNR22wN567Yx5cJ0sIN7wB5X+91uttJ0Azn2IsiER/I2wzBDV19XqJ9j0bEiwGJwb898mgSSU2+gH8ousdQeP8lqa9NT+u20dSch+nPHtfZl/5lAoFuaKLXVN/WpqZQ6SOdOkhVJuCct8HX/S4YNL/VhErl9974qHPKyezkkBnKsZOxqLe/0K1Jzqlf2osArrPVia/R/6XxUJZjDigFxekNf5MWCnACARC/o2ZLQWWgUpBcixaY2wqGNSdyZg8+4KpcEcERWs//guEI/BwsqyQhwKW2p+Q3UYHKgZ35i8TEtCfBLKw== adb42@gmail.com
```
Now log out and see if you can jump to the host without the password:
#### Jump to the sw server
The following output greets you without asking a password, once you have added your public key to the .ssh folder as described above:
```
$ make jump
Welcome to Ubuntu 22.04.1 LTS (GNU/Linux 5.15.0-50-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/advantage

  System information as of Thu 13 Oct 13:27:14 UTC 2022

  System load:  0.0                 Processes:               285
  Usage of /:   10.1% of 147.49GB   Users logged in:         0
  Memory usage: 1%                  IPv4 address for ens160: 10.20.7.7
  Swap usage:   0%

 * Super-optimized for small spaces - read how we shrank the memory
   footprint of MicroK8s to make it the smallest full K8s around.

   https://ubuntu.com/blog/microk8s-memory-optimisation

12 updates can be applied immediately.
1 of these updates is a standard security update.
To see these additional updates run: apt list --upgradable


Last login: Thu Oct 13 13:26:11 2022 from 10.20.7.11
a.debeer@za-itf-sw:~$ 
```

## Run iTango (an interactive Tango session) on the SW Server

### Prerequisites
Ensure you have [k9s](https://k9scli.io/topics/install/) installed, and that remote access to the SW host is established.

#### Copy the KUBECONFIG file
The KUBECONFIG file enables access to the cluster resources. Copy it using SSH Copy:
```
$ make copy-kubeconfig
```
You can run the `k9s` app with the correct KUBECONFIG loaded and pointing at your desired namespace, all in one go, with the `make` command:
```
$ make k9s
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
