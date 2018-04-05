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

- `packages`: The packages to be installed. Subkeys:

    + `preliminary`: These are installed after the update but before everything
      else. Things that are required for adding keys etc (like
      `apt-transport-https`) should be under this key.

    + `x`: Packages to be installed if the system has a running X system, i.e.
      if it's a desktop OS. This distinction is made based on the availability
      of the environment variable `XDG_CURRENT_DESKTOP`.

    + `no-x`: Packages to be installed if it's a server system.

- `apt-repos`: The apt repositories to add.

- `git-repos`: The repos to be checked out. This should be a list, with each
  element another list of length two, the first item being the Git URL, and the
  second the location to checkt out to.