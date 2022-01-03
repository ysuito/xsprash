# xsprash
A Rootless, Seamless, Stateless Development Environment.

# Build a local environment

Install docker rootless, following the instructions below.

https://docs.docker.jp/engine/security/rootless.html

For bash, add the following to `~/.bash_profile`

```bash:~/.bash_profile
export PATH=$HOME/bin:$PATH
export DOCKER_HOST=unix://$XDG_RUNTIME_DIR/docker.sock
```

For fish
```bash:bash
$ set -U fish_user_paths ~/bin $fish_user_paths
$ set -Ux DOCKER_HOST unix://$XDG_RUNTIME_DIR/docker.sock
```

Please log out and log back in.

Check if docker rootless works.
```bash:bash
$ docker ps
CONTAINER ID  IMAGE  COMMAND  CREATED  STATUS  PORTS  NAMES
```

The next step is to install x11docker.
First, install the recommended packages for each distribution.

https://github.com/mviereck/x11docker/wiki/Dependencies#recommended-base

If you have Arch Linux, you can use

```bash:bash
sudo pacman -S xpra xorg-server-xephyr xorg-xinit xorg-xauth xclip xorg-xhost xorg-xrandr xorg-xdpyinfo nxagent glu
```
I also installed `glu` for GPU support of xpra.

After the dependencies are installed, install x11docker itself.

```bash:bash
curl -fsSL https://raw.githubusercontent.com/mviereck/x11docker/master/x11docker | sudo bash -s -- --update
```

## System Settings
Change the configuration so that X Server can be started from X11docker.

```bash:bash
echo "allowed_users=anybody" | sudo tee -a /etc/X11/Xwrapper.config
```

Change the configuration so that you can connect to DBUS from within the container.
Create a `/usr/share/dbus-1/session.d/session-local.conf`

```config:/usr/share/dbus-1/session.d/session-local.conf
<!DOCTYPE busconfig PUBLIC "-//freedesktop//DTD D-Bus Bus Configuration 1.0//EN"
 "http://www.freedesktop.org/standards/dbus/1.0/busconfig.dtd">
<busconfig>
  <auth>ANONYMOUS</auth>
  <allow_anonymous/>
</busconfig>
```

Build xpra image and vscode image.

```bash:bash
$ git clone https://github.com/ysuito/xsprash.git
$ docker build -t ubuntubase xsprash/src/ubuntubase_ja/
$ docker build -t xpra xsprash/src/xpra/
$ docker build -t vscode xsprash/src/vscode/
```

There are definitions of other applications under `src/`, but we have only built the one above as a sample.

```bash:bash
$ docker images
REPOSITORY                                           TAG               IMAGE ID       CREATED        SIZE
vscode                                               latest            5419f3b23f23   41 hours ago   1.6GB
xpra                                                 latest            dcede0d68d1e   41 hours ago   1.49GB
ubuntu                                               latest            ba6acccedd29   2 months ago   72.8MB
```

Define the application to configure the resources to be used by the application.

```bash:bash
$ python xsprash.py create
App Name(String):vscode
Image(String):vscode
Command(String):code --verbose --no-sandbox --user-data-dir=/root/.config/Code
Audio(y/N):n
Input Method(y/N):y
Volume(y/N):y
Share Docker Socket(y/N):y
Share tmpfs /dev/shm(y/N):y
Share gpu /dev/dri(y/N):y
Share kvm /dev/kvm(y/N):n
Docker Options(String):
```

If you want to register it as a gnome desktop app, put your favorite icon file in `icon/` and execute the following.

```bash:bash
$ python xsprash.py desktop-entry vscode
Icon File:vscode.svg
```
Now, you can use it as a gnome desktop application.

If you want to start it from the command line, run the following.
```bash:bash
$ python xsprash.py aliases
alias vscode='python $HOME/xsprash/xsprash.py start vscode'
```

The alias setting will be output, so add it to the alias configuration file of your shell.

This will start the vscode running on the container.

```bash:bash
$ vscode
```

If you are developing with vscode Remote Container, add the following settings to `devcontainer.json`.

```json:devcontainer.json
	"remoteUser": "root",
	"workspaceMount": "source=${localEnv:BIND_PATH}/${localWorkspaceFolderBasename},target=/workspace,type=bind,consistency=cached",
	"workspaceFolder": "/workspace"
```

Now you can start vscode on the local side.

# Build the remote server

Perform the same steps as for building the local environment.

In addition, add the following contents to `~/.profile`.
```bash:~/.profile
export PATH=$HOME/bin:$PATH
export DOCKER_HOST=unix://$XDG_RUNTIME_DIR/docker.sock
```

This completes the building of the remote server.
If the remote server is a PC with a screen and keyboard, you can launch the application locally by executing `vscode`.

# SSH configuration

Replace the IP_ADDRESS, USERNAME, KEY, and SHELL parts with your environment.

```config:~/.ssh/config
Host dev-server
HostName       IP_ADDRESS
Port           22
User           USERNAME
IdentityFile   ~/.ssh/KEY
RequestTTY     force
RemoteCommand  source ~/.profile; python ~/xsprash/xsprash.py server & SHELL
PermitLocalCommand yes
LocalCommand   python ~/xsprash/xsprash.py client &
LocalForward   10000 127.0.0.1:10000
```

## Point

- RemoteCommand starts xpra server remotely and launch a shell
- LocalCommand starts the xpra client locally.

Now let's connect to the server from the client.

```
ssh dev-server
```

When prompted by the server

```
vscode
```
When you log out from the remote, you can exit by typing `exit` once in normal ssh, but you need to do `Ctrl+c` again because LocalCommand is still active.

Now you can use vscode running on remote machine in local pc.
In this state, the local and remote directories are not shared.
In the following sections, we will explain how to share the persistent data area between local and remote.

# Configure file synchronization with Syncthing

We will use the official syncthing Docker Image and modify the ssh config settings.

```config:~/.ssh/config
Host dev-server
HostName       IP_ADDRESS
Port           22
User           USERNAME
IdentityFile   ~/.ssh/KEY
RequestTTY     force
RemoteCommand  source ~/.profile; python ~/xsprash/xsprash.py server & docker run -p 8384:8384 -p 22000:22000/tcp -p 22000:22000/udp -v ~/xsprash/volume:/var/syncthing --hostname=dev-server -e PUID=0 -e PGID=0 syncthing/syncthing  > ~/xsprash/log/syncthing.log 2>&1 & SHELL
PermitLocalCommand yes
LocalCommand   python ~/xsprash/xsprash.py client & docker run --rm -p 8384:8384/tcp -p 22000:22000/tcp -p 22000:22000/udp -v ~/xsprash/volume:/var/syncthing --hostname=local-pc -e PUID=0 -e PGID=0 docker.io/syncthing/syncthing  > ~/xsprash/log/syncthing.log 2>&1 &
LocalForward   10000 127.0.0.1:10000
LocalForward   18384 127.0.0.1:8384
```

If you access the following address with a browser, you can set up synchronization.
See the Syncthing documentation for details.

https://docs.syncthing.net/

Local Syncthing： `http://127.0.0.1:8384`

Remote Syncthing： `http://127.0.0.1:18384`

## Syncthing Configuration Simplified Flow

- Add devices to each other
- Add the directory you want to share under `~/xsprash/volume/` and set up sharing.

If you enable UPnP on the NAT router on the route, you will get a direct connection and the network will be faster.
Even if UPnP is disabled, you can still share files via the Relay server.

# Configure file synchronization using SSHFS

If the UIDs of the local side and the remote side do not match, the permissions will be misaligned and you will not be able to use this method.

## Local side

Run sshd on the client side and add authorized_keys for the user
If you are concerned about security, you can use

```config:/etc/ssh/sshd_config
ListenAddress 127.0.0.1
ListenAddress ::1
```

to limit the IPs that can be ssh-logged into to local IPs.

Carry the client's private key to the server and execute the following.

## Server side

Install SSHFS.

```
sudo apt install sshfs
```

Add the following to `~/.ssh/config`; change the LOCALPC, USER, and LOCALPCKEY parts accordingly.

```config:~/.ssh/config
Host           LOCALPC
HostName       127.0.0.1
Port           2222
User           USER
IdentityFile   ~/.ssh/LOCALPCKEY
```

If this is the first time you have created a config file, run the following.

```
chmod 600 ~/.ssh/config
```

Once you have connected to the client, add the fingerprint to known_hosts.

```
ssh LOCALPC
```

## Client side

Modify ssh config

```config:~/.ssh/config
Host dev-server
HostName       IP_ADDRESS
Port           22
User           USERNAME
IdentityFile   ~/.ssh/KEY
RequestTTY     force
RemoteCommand  source ~/.profile; python ~/xsprash/xsprash.py server & sshfs LOCALPC:xsprash/volume ~/xsprash/volume > ~/xsprash/log/sshfs.log 2>&1 &  SHELL
PermitLocalCommand yes
LocalCommand   python ~/xsprash/xsprash.py client &
RemoteForward  2222 127.0.0.1:22
LocalForward   10000 127.0.0.1:10000
```

# File synchronization pattern

- No synchronization (local and remote are separate)
- SSHFS to mount local directory to remote (no time lag, low throughput)
- Syncthing to synchronize local and remote directories (with time lag, high throughput)

# server-side firewall settings

## When using Syncthing

## Inbound

- From: Local side global IP To: Server IP Port: 22000/udp
- From:Local side Global IP To:Server IP Port:22000/tcp
- From:Local side Global IP To:Server IP Port:22/tcp

### Outbound

- From:Server IP To:Any Port:Any

### SSHFS, without file synchronization.

### Inbound

- From:Local side Global IP To:Server IP Port:22/tcp

### Outbound

- From:Server IP To:Any Port:Any

### How to switch the environment

- If you start the application at the ssh prompt, you will be in the remote environment.
- If you start the application in a local terminal, you will be in the local environment.
