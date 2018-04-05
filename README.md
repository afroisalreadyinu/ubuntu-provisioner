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

Add a file `config.json` into the same directory as the `provision.py` script
(format of `config.json` documented below). Afterwards, run `python3.6
provision.py pack`. This will produce a file (encrypted, if you have openssl
installed) that contains the following, zipped:

- `provision.py`

- The SSH key files (private and accompanying public files) from the `~/.ssh`
  directory.

- `config.json`

When you want to provision a new computer, copy this seed to that computer,
decrypt and unpack it. Then run `python3.6 provision.py run`.

## config.json contents

- `packages`: The packages to be installed. Subkeys:

    + `preliminary`: These are installed after the update but before everything
      else. Things that are required for adding keys etc (like
      `apt-transport-https`) should be under this key.

    + `x`: Packages to be installed if the current shell is running in a
      windowing system, i.e. if it's a desktop OS. This distinction is made
      based on the availability of the environment variable
      `XDG_CURRENT_DESKTOP`.

    + `no-x`: Packages to be installed if the current shell is not running in a
      windowing system.

- `apt-repos`: The apt repositories to add. A list of dictionaries. Each
  dictionary should have the key `repo_spec`, a repo specification in the format
  `apt-add-repository` accepts, and either `key_url` for the gpg key, or
  `keyserver` and `recv_keys` to download the key.

- `git-repos`: The repos to be checked out. List of lists of length two, the
  first item being the Git URL, and the second the location to check out to.

- `binaries`: Binary files to install as executables to `/usr/local/bin`. List
  of lists of length two. First item is the URL of the file, second is how it
  should be named locally.

- `executable-from-repo`: List of repository URLs that should be installed. The
  repository is cloned to `/tmp`, then compiled and installed with `autoconf`,
  `configure` and `sudo make install`. The local clone is then deleted.

- `kubeconfig`: Kubernetes configurations to download. List of lists of length
  two. The first item is the Kubernetes primary server to download the
  configuration from, the second is under which name it should be saved in
  `~/.kube`.
