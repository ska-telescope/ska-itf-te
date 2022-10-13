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
#### Jump to the sw host server
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



## Getting started

The following is provided by Gitlab:

To make it easy for you to get started with GitLab, here's a list of recommended next steps.

Already a pro? Just edit this README.md and make it your own. Want to make it easy? [Use the template at the bottom](#editing-this-readme)!

## Add your files

- [ ] [Create](https://docs.gitlab.com/ee/user/project/repository/web_editor.html#create-a-file) or [upload](https://docs.gitlab.com/ee/user/project/repository/web_editor.html#upload-a-file) files
- [ ] [Add files using the command line](https://docs.gitlab.com/ee/gitlab-basics/add-file.html#add-a-file-using-the-command-line) or push an existing Git repository with the following command:

```
cd existing_repo
git remote add origin https://gitlab.com/ska-telescope/ska-itf-te.git
git branch -M main
git push -uf origin main
```

## Integrate with your tools

- [ ] [Set up project integrations](https://gitlab.com/ska-telescope/ska-itf-te/-/settings/integrations)

## Collaborate with your team

- [ ] [Invite team members and collaborators](https://docs.gitlab.com/ee/user/project/members/)
- [ ] [Create a new merge request](https://docs.gitlab.com/ee/user/project/merge_requests/creating_merge_requests.html)
- [ ] [Automatically close issues from merge requests](https://docs.gitlab.com/ee/user/project/issues/managing_issues.html#closing-issues-automatically)
- [ ] [Enable merge request approvals](https://docs.gitlab.com/ee/user/project/merge_requests/approvals/)
- [ ] [Automatically merge when pipeline succeeds](https://docs.gitlab.com/ee/user/project/merge_requests/merge_when_pipeline_succeeds.html)

## Test and Deploy

Use the built-in continuous integration in GitLab.

- [ ] [Get started with GitLab CI/CD](https://docs.gitlab.com/ee/ci/quick_start/index.html)
- [ ] [Analyze your code for known vulnerabilities with Static Application Security Testing(SAST)](https://docs.gitlab.com/ee/user/application_security/sast/)
- [ ] [Deploy to Kubernetes, Amazon EC2, or Amazon ECS using Auto Deploy](https://docs.gitlab.com/ee/topics/autodevops/requirements.html)
- [ ] [Use pull-based deployments for improved Kubernetes management](https://docs.gitlab.com/ee/user/clusters/agent/)
- [ ] [Set up protected environments](https://docs.gitlab.com/ee/ci/environments/protected_environments.html)

***

# Editing this README

When you're ready to make this README your own, just edit this file and use the handy template below (or feel free to structure it however you want - this is just a starting point!).  Thank you to [makeareadme.com](https://www.makeareadme.com/) for this template.

## Suggestions for a good README
Every project is different, so consider which of these sections apply to yours. The sections used in the template are suggestions for most open source projects. Also keep in mind that while a README can be too long and detailed, too long is better than too short. If you think your README is too long, consider utilizing another form of documentation rather than cutting out information.

## Name
Choose a self-explaining name for your project.

## Description
Let people know what your project can do specifically. Provide context and add a link to any reference visitors might be unfamiliar with. A list of Features or a Background subsection can also be added here. If there are alternatives to your project, this is a good place to list differentiating factors.

## Badges
On some READMEs, you may see small images that convey metadata, such as whether or not all the tests are passing for the project. You can use Shields to add some to your README. Many services also have instructions for adding a badge.

## Visuals
Depending on what you are making, it can be a good idea to include screenshots or even a video (you'll frequently see GIFs rather than actual videos). Tools like ttygif can help, but check out Asciinema for a more sophisticated method.

## Installation
Within a particular ecosystem, there may be a common way of installing things, such as using Yarn, NuGet, or Homebrew. However, consider the possibility that whoever is reading your README is a novice and would like more guidance. Listing specific steps helps remove ambiguity and gets people to using your project as quickly as possible. If it only runs in a specific context like a particular programming language version or operating system or has dependencies that have to be installed manually, also add a Requirements subsection.

## Usage
Use examples liberally, and show the expected output if you can. It's helpful to have inline the smallest example of usage that you can demonstrate, while providing links to more sophisticated examples if they are too long to reasonably include in the README.

## Support
Tell people where they can go to for help. It can be any combination of an issue tracker, a chat room, an email address, etc.

## Roadmap
If you have ideas for releases in the future, it is a good idea to list them in the README.

## Contributing
State if you are open to contributions and what your requirements are for accepting them.

For people who want to make changes to your project, it's helpful to have some documentation on how to get started. Perhaps there is a script that they should run or some environment variables that they need to set. Make these steps explicit. These instructions could also be useful to your future self.

You can also document commands to lint the code or run tests. These steps help to ensure high code quality and reduce the likelihood that the changes inadvertently break something. Having instructions for running tests is especially helpful if it requires external setup, such as starting a Selenium server for testing in a browser.

## Authors and acknowledgment
Show your appreciation to those who have contributed to the project.

## License
For open source projects, say how it is licensed.

## Project status
If you have run out of energy or time for your project, put a note at the top of the README saying that development has slowed down or stopped completely. Someone may choose to fork your project or volunteer to step in as a maintainer or owner, allowing your project to keep going. You can also make an explicit request for maintainers.
