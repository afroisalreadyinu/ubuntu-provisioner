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
