# ubuntu-provisioner

I wrote this script after my work laptop was borked twice in a week, and I had
to spend an unnecessary amount of time re-installing and setting up stuff. Using
a configuration file, this script can

- Install apt packages, binary files, or code projects from Git repositories

- Add repositories with keys

- Add ssh keys

- Check out git repositories

- Fetch kubernetes configurations

The script is quite hacky, and still in development, but should be usable as-is,
since I make sure to run it regularly.

# Flow

The script does the following right now (edit the `main` function to customize):

- Update and upgrade. User is prompted for reboot if it is necessary.

- Install preliminary packages

- Copy ssh keys, add them to agent

- Install all other packages

- Check out repos

- Install binaries

- Install executables from repos

- Fetch Kubernetes configurations


## Usage

Add a file `config.json` with the following keys:

- packages: The packages to be installed. Subkeys:

    + preliminary: These are installed after the update but before everything
      else. Things that are required for adding keys etc (like
      `apt-transport-https`) should be under this key.
