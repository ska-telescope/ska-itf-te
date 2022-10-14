# ska-itf-te
To get that nice output at the beginning of the command line, add the following to your .bashrc:
```
parse_git_branch() {
    git branch 2> /dev/null | sed -e '/^[^*]/d' -e 's/* \(.*\)/ (\1)/'
}

export PATH="/usr/local/mysql/bin:$PATH"
export PS1="\u@\h \W\[\033[32m\]\$(parse_git_branch)\[\033[00m\] $ "
```
Alternatively (especially if you're using ZSH!), you can use one of the useful profiles from oh-my-zsh: install it from https://ohmyz.sh/

## Makefile for SW server access
A subset of the makefile commands available in the [Deploy Mid ITF](https://gitlab.com/ska-telescope/sdi/ska-cicd-deploy-low-itf) have been added to the resources folder.

#### PRO TIP: ALWAYS ADD ` --dry` TO THE END OF A MAKE COMMAND IF YOU WANT TO SEE WHAT IT IS GOING TO TRY TO DO.

### Prerequisites

You need to set one `make` variable in order to use your own acces pattern. Do that with this command, substituting `<your-initials>` with your initials which are also the foldernames under `resources/users/`:
```
$ echo ME=<your-initials> >> resources/users/UserProfile.mak
```
Test if this worked, by verifying your name shows up when you ask that existential question:
```
$ make whoami
    User b.lunsky
```
#### Set up passwordless SSH access
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