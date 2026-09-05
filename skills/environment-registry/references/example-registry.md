# Worked example: an environment-registry memory

Adapted and generalized from a real project's VM-registry memory, showing the pattern applied to
VirtualBox VMs — the same shape applies to containers, staging servers, or physical devices.

Real environments on this host, checked live via `VBoxManage list vms`:

    "staging-vm"    {5d9651d9-...}
    "test-vm-A"     {e4fe8e9f-...}

## Credentials policy

Never store, ask for, or type an actual password. Every account below is reached via SSH key;
passwordless sudo is set up for the accounts listed. If a task ever needs an account without this,
sudo needs the human to type their own password live into that environment's own window — never
asked for in chat, never typed on their behalf, never recorded here.

## test-vm-A — SSH access

    ssh -i ~/.ssh/dev_vm_key -p 2222 devuser@localhost

## Known gotchas (cost real debugging time — read before repeating the mistake)

- **Clipboard between host and guest is unreliable.** Confirmed live; a Guest-Additions version
  mismatch was found and fixed but didn't resolve it — root cause is a known VirtualBox limitation
  on this guest OS. Don't rely on paste for getting content into the VM; type directly or drive
  input programmatically instead.
- **GUI focus silently drifts back to the host client between actions.** Always confirm the target
  window is focused immediately before typing or clicking — a real, observed failure mode where
  commands landed nowhere until this check was added.
