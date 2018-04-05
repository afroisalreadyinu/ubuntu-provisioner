import os
import sys
import subprocess
from getpass import getpass
import shutil
import shlex
from urllib import request
from pathlib import Path
import hashlib
from zipfile import ZipFile
import json

CURRENT_DIR = Path(".").resolve()
HOME = Path('~/').expanduser()

with open('/etc/lsb-release', 'r') as release_file:
    RELEASE_CODENAME = [line.split('=', 1)[1].strip() for line in release_file.readlines()
                         if 'DISTRIB_CODENAME' in line][0]


bcolors = dict(
    header='\033[95m',
    blue='\033[94m',
    green='\033[92m',
    warning='\033[93m',
    red='\033[91m',
    endc='\033[0m',
    bold='\033[1m',
    underline='\033[4m'
)


def colorit(color, text):
    return '{}{}{}'.format(bcolors[color], text, bcolors['endc'])

def cache_sudo_pass():
    while True:
        sudo_pass = getpass("sudo password: ")
        proc = subprocess.Popen(["sudo", "-S", "ls", "/tmp"],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                stdin=subprocess.PIPE,
                                universal_newlines=True)
        out, err = proc.communicate(sudo_pass + "\n")
        if err and (proc.returncode != 0):
            print("Looks like the password was not correct")
        else:
            return

def run_cmd(cmd_parts, intro_msg=None, error_msg=None, **kwargs):
    if intro_msg: print(intro_msg)
    proc = subprocess.Popen(cmd_parts,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            stdin=subprocess.PIPE,
                            universal_newlines=True,
                            **kwargs)
    out, err = proc.communicate()
    if proc.returncode != 0:
        if error_msg:
            print(error_msg)
            print(err)
    return proc.returncode



def add_repo(repo_spec, key_url=None, keyserver=None, recv_keys=None):
    repo_spec = repo_spec.format(RELEASE_CODENAME=RELEASE_CODENAME)
    if key_url:
        key_path = Path('/tmp') / hashlib.md5(key_url.encode()).hexdigest()
        with request.urlopen(key_url) as response, \
             open(key_path, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
        run_cmd(["sudo", "apt-key", "add", key_path],
                colorit('blue', f"Adding key from {key_url}"))
    elif (keyserver and recv_keys):
        run_cmd(["sudo", "apt-key", "adv", "--keyserver", keyserver,
                 "--recv-keys", recv_keys])
    run_cmd(["sudo", "add-apt-repository",  "-y", repo_spec],
            colorit('blue', f"Adding apt repo {repo_spec}"),
            colorit('red', "Failed to add repo url"))
    run_cmd(["sudo", "apt", "update"])


def install_packages(package_list):
    code = run_cmd(["sudo", "apt",  "-y", "install"] + package_list,
                   colorit('blue', f"Installing {len(package_list)} packages"),
                   colorit("red", "Not all packages could be installed, stopping"))
    return code == 0

def install_single_package(package_name):
    code = run_cmd(["sudo", "apt", "-y", "install", package_name],
                   colorit('blue', f"Installing {package_name}"),
                   colorit("red", f"{package_name} could not be installed"))
    return code == 0


def install_binary(file_url, filename):
    file_path = Path('/usr/local/bin') / filename
    if file_path.exists():
        yesno = input("File %s exists, override? [yN] " % file_path)
        if yesno not in ['y', 'Y']:
            return
    tmp_path = Path('/tmp') / filename
    with request.urlopen(file_url) as response, \
          open(tmp_path, 'wb') as out_file:
        shutil.copyfileobj(response, out_file)
    if tmp_path.suffix in [".zip", ".tgz", ".gz"]:
        run_cmd(["unp", str(tmp_path)])
        tmp_path = tmp_path.with_suffix('')
    run_cmd(["chmod", "+x", str(tmp_path)])
    run_cmd(["sudo", "mv", str(tmp_path), str(file_path)])

def install_executable_from_repo(repo_url):
    repo_path = Path('/tmp') / hashlib.md5(repo_url.encode()).hexdigest()
    if not repo_path.exists():
        run_cmd(["git", "clone", repo_url, repo_path])
    run_cmd(["autoconf"], cwd=str(repo_path))
    run_cmd(["./configure"], cwd=str(repo_path))
    run_cmd(["sudo", "make", "install"], cwd=str(repo_path))


def check_out_repos(repos):
    for repo_url, dir_path in repos:
        target_dir = HOME /  dir_path
        if target_dir.exists():
            print(colorit("warning", "Directory {} exists, skipping".format(target_dir)))
            continue
        else:
            subprocess.call(["git", "clone", repo_url, str(target_dir)])


def install_ssh_keys():
    ssh_keys_dir = HOME / ".ssh"
    if not ssh_keys_dir.is_dir():
        ssh_keys_dir.mkdir()
    ssh_files_dir = CURRENT_DIR / "ssh_keys"
    for ssh_file in ssh_files_dir.iterdir():
        path = ssh_keys_dir / ssh_file.name
        if not path.exists():
            shutil.copy(ssh_file, path)
        else:
            print(colorit("blue", "SSH file {} exists, skipping".format(ssh_file.name)))
    with subprocess.Popen(["ssh-agent", "-s"], stdout=subprocess.PIPE) as proc:
        lines = proc.stdout.read().decode()
        for part in shlex.split(lines):
            if '=' in part:
                key, value = part.split('=', 1)
                os.environ[key] = value.strip(' \n;')
    for key_file in ssh_keys_dir.glob('*.pub'):
        if key_file.with_suffix('').exists():
            # both public and private file exist, add to agent
            subprocess.call(["ssh-add", str(key_file.with_suffix(''))])
    return lines

def copy_kubeconfig(origin_server, local_config_name):
    kube_dir = HOME / ".kube"
    kube_dir.mkdir(exist_ok=True)
    file_path = kube_dir / local_config_name
    if file_path.exists():
        colorit('green', f"Kubernetes config {local_config_name} already exists, skipping")
        return
    from_ = f"{origin_server}:~/.kube/config"
    run_cmd(["scp", from_, str(file_path)],
            colorit('blue', f"Adding Kubernetes config from {origin_server}"),
            colorit('red', f"Kubernetes config from {origin_server} could not be copied"))


def main(config, x_or_no):
    cache_sudo_pass()
    run_cmd(["sudo", "apt", "update"], colorit('blue', 'Updating packages'))
    run_cmd(["sudo", "apt", "-y", "upgrade"], colorit('blue', 'Upgrading'))

    if os.path.exists("/var/run/reboot-required"):
        print(colorit("red", "You need to reboot"))
        return
    install_ssh_keys()

    if not install_packages(config['packages']['preliminary']):
        return

    for entry in config['repos']:
       add_repo(**entry)

    check_out_repos(config['git-repos'])

    for url, cmd_name in config['binaries']:
        install_binary(url, cmd_name)

    for repo_url in config['executable-from-repo']:
        install_executable_from_repo(repo_url)
    for main_url, config_name in config['kubeconfig']:
        copy_kubeconfig(main_url, config_name)


def pack():
    provisioner_dir = CURRENT_DIR / "provisioner"
    provisioner_dir.mkdir(exist_ok=True)
    shutil.copy(__file__, str(provisioner_dir))
    ssh_local = provisioner_dir / "ssh_files"
    ssh_local.mkdir(exist_ok=True)
    ssh_home = HOME / ".ssh"
    file_names = []
    for public_key in ssh_home.glob("*.pub"):
        private_key = public_key.with_suffix('')
        if private_key.exists():
            #copy both files to ssh_files
            file_names.append(public_key.name)
            shutil.copy(str(public_key), str(ssh_local / public_key.name))
            file_names.append(private_key.name)
            shutil.copy(str(private_key), str(ssh_local / private_key.name))
    with ZipFile("provisioner.zip", 'w') as out_zip:
        out_zip.write("provisioner/provision.py")
        out_zip.write("provisioner/ssh_files")
        for file_name in file_names:
            out_zip.write(f"provisioner/ssh_files/{file_name}")
    shutil.rmtree(str(provisioner_dir))

def read_config():
    with open(CURRENT_DIR / 'config.json', 'r') as json_file:
        config = json.loads(json_file.read())
    return config

USAGE = "Usage: python3 provision.py pack | run --no-x/--x"

def _main():
    if len(sys.argv) < 2:
        print(USAGE)
        return
    command = sys.argv[1]
    if command not in ['pack', 'run']:
        print(USAGE)
        return
    if command == 'pack':
        pack()
    else:
        if sys.argv[2] not in ["--x", "--no-x"]:
            print(USAGE)
            return
        config = read_config()
        x_or_no = sys.argv[1] == "--x"
        main(config, x_or_no)


if __name__ == "__main__":
    _main()
