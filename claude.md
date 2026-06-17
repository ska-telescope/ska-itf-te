# Ansible Chat History

## Tagging tasks with `spfrx`

**Q:** How to use tags to only run `main.yml` when using the tag `spfrx`?

**A:** Add `tags: [spfrx]` to the task. For `include_tasks`, also use `apply.tags` to propagate the tag into included tasks:

```yaml
- name: Update SPFRx
  ansible.builtin.include_tasks:
    file: network.yml
    apply:
      tags:
        - spfrx
  tags:
    - spfrx
```

Run with:
```bash
ansible-playbook <your-playbook>.yml --tags spfrx
```

---

## Listing tasks / sub-commands

```bash
# List all tasks (with tag filter)
ansible-playbook -i inventory/hosts-template --limit spfrx site.yml --tags spfrx --list-tasks

# List available tags
ansible-playbook -i inventory/hosts-template --limit spfrx site.yml --list-tags
```

`--list-tags` only shows tag names; `--list-tasks` shows expanded task names.

---

## Dynamic include vs static import

`include_tasks` is dynamic — Ansible resolves it at runtime, so `--list-tasks` cannot expand subtasks from included files.

`import_tasks` is static — resolved at parse time, so `--list-tasks` shows all nested tasks.

**Rule of thumb:**
- Use `include_tasks` when you need runtime branching or loops.
- Use `import_tasks` when structure is fixed and you want better introspection.

---

## Switching to static import (when no loop is needed)

```yaml
- name: Update SPFRx
  ansible.builtin.import_tasks: network.yml
  tags:
    - spfrx
```

---

## spfrx_setup role — final structure

The role was refactored from a dynamic discovery loop to two explicit static imports for the two known network files.

### `roles/spfrx_setup/tasks/main.yml`

```yaml
- name: Create backup dir
  ansible.builtin.file:
    path: "{{ backup_dir }}"
    state: directory
    mode: '0755'
  tags:
    - spfrx

- name: Update DNS in 00-eth.network
  ansible.builtin.import_tasks: network.yml
  vars:
    network_path: "{{ network_dir }}/00-eth.network"
  tags:
    - spfrx

- name: Update DNS in 10-eth.network
  ansible.builtin.import_tasks: network.yml
  vars:
    network_path: "{{ network_dir }}/10-eth.network"
  tags:
    - spfrx

- name: Restart networking
  ansible.builtin.systemd:
    state: restarted
    daemon_reload: true
    name: systemd-networkd.service
  become: true
  tags:
    - spfrx
```

### `roles/spfrx_setup/tasks/network.yml`

```yaml
- name: Backup existing file
  ansible.builtin.copy:
    remote_src: true
    src: "{{ network_path }}"
    dest: "{{ backup_dir }}/{{ network_path | basename }}.backup"
    owner: root
    group: root
    force: false
    mode: preserve

# --- 00-eth.network: comment everything, append full static block ---

- name: Comment out existing non-comment lines in 00-eth.network
  ansible.builtin.replace:
    path: "{{ network_path }}"
    regexp: '^(?!#)(.+)$'
    replace: '# \1'
  when: network_path | basename == "00-eth.network"

- name: Append static SPFRx block to 00-eth.network
  ansible.builtin.blockinfile:
    path: "{{ network_path }}"
    marker: "# {mark} ANSIBLE MANAGED BLOCK: SPFRX 00-eth.network"
    block: |
      [Match]
      Name=eth0

      [Address]
      Address=10.160.100.5/26

      [Network]
      Netmask=255.255.255.192
      Network=10.160.100.0
      Gateway=10.160.100.62
      DNS=10.81.228.213
      DNS=10.81.228.214

      [Link]
      MACAddress=00:11:22:33:44:05
    insertafter: EOF
  when: network_path | basename == "00-eth.network"

# --- 10-eth.network: comment everything, then uncomment allowlist lines ---

- name: Comment out existing non-comment lines in 10-eth.network
  ansible.builtin.replace:
    path: "{{ network_path }}"
    regexp: '^(?!#)(.+)$'
    replace: '# \1'
  when: network_path | basename == "10-eth.network"

- name: Uncomment allowlist lines in 10-eth.network
  ansible.builtin.replace:
    path: "{{ network_path }}"
    regexp: '^# (Name=eth1|\[Address\]|MTUBytes=4000|\[Link\]|Address=192\.168\.8\.53/16|\[Network\])$'
    replace: '\1'
  when: network_path | basename == "10-eth.network"
```

**Allowlist for `10-eth.network`** (all other lines stay commented):
- `Name=eth1`
- `[Address]`
- `MTUBytes=4000`
- `[Link]`
- `Address=192.168.8.53/16`
- `[Network]`

---

## Running the playbook

```bash
# Dry-run / check mode (safe)
ansible-playbook -i inventory/hosts-template --limit spfrx site.yml --tags spfrx --check -vv

# List tasks for spfrx play
ansible-playbook -i inventory/hosts-template --limit spfrx site.yml --tags spfrx --list-tasks

# Execute
ansible-playbook -i inventory/hosts-template --limit spfrx site.yml --tags spfrx
```
