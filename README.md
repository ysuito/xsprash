# xsprash
A Rootless, Seamless, Stateless Development Environment.

[Japanese README](README_ja.md) is also available.

## Supported System
xsprash runs on Linux.

## Features
Enables GUI applications to run on Linux containers.
Supports screen display, audio output, and input methods.

### Rootless
All containers run in rootless mode, which means they never need root privileges after they are built.
Each container's home directory is bound to a single location on the host, keeping the host environment clean and uncluttered.

### Seamless
Simply connect via ssh and launch the app to see the app running on another PC or server locally.
Easily run high-integrity processes on your laptop.

### Stateless
All but the bound home directory is destroyed when the app exits, making the environment highly repeatable.
It is very easy to move to another PC.


## Installation
### Docker Rootless
Install docker rootless according to [Run the Docker daemon as a non-root user](https://docs.docker.com/engine/security/rootless/)

### x11docker
Install dependancies for x11docker according to [recommended-base](https://github.com/mviereck/x11docker/wiki/Dependencies#recommended-base)

Install x11docker itself
```bash:bash
curl -fsSL https://raw.githubusercontent.com/mviereck/x11docker/master/x11docker | sudo bash -s -- --update
```

### System Settings
Change the configuration so that X Server can be started from X11docker.

```config:/etc/X11/Xwrapper.config
...
allowed_users=anybody
```

Change the configuration so that you can connect to DBUS from within the container.
Create `/usr/share/dbus-1/session.d/session-local.conf`

```config:/usr/share/dbus-1/session.d/session-local.conf
<!DOCTYPE busconfig PUBLIC "-//freedesktop//DTD D-Bus Bus Configuration 1.0//EN"
 "http://www.freedesktop.org/standards/dbus/1.0/busconfig.dtd">
<busconfig>
  <auth>ANONYMOUS</auth>
  <allow_anonymous/>
</busconfig>
```

### image build

Build a vscode image

```bash:bash
git clone https://github.com/ysuito/xsprash.git
cd xsprash
docker build -t ubuntubase src/ubuntubase/
docker build -t vscode src/vscode/
```
For Japanese environment, change `ubuntubase` to `ubuntubase_ja`.
There are definitions of other applications under `src/`, but only the one above is built for the sake of sample.

### Application definition

Define the application to configure the resources to be used by the application.
```bash:bash
$ python3 xsprash.py create
App Name(String):vscode
Image(String):vscode
Command(String):code --verbose
Audio(y/N):y
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
$ python3 xsprash.py desktop-entry vscode
Icon File:vscode.svg
```
Now, you can use it as a gnome desktop application.

If you want to start it from the command line, run the following.
```bash:bash
$ python3 xsprash.py aliases
alias vscode='python3 /home/$USER/xsprash/xsprash.py start vscode'
```

The alias setting will be output, so add it to the alias configuration file of your shell.

Now you can start vscode running on the container.

```bash:bash
vscode
```

If you are developing with vscode Remote Container, add the following settings to `devcontainer.json`.

```json:devcontainer.json
	"remoteUser": "vscode",
	"workspaceMount": "source=${localEnv:BIND_PATH}/${localWorkspaceFolderBasename},target=/workspace,type=bind,consistency=cached",
	"workspaceFolder": "/workspace"
```

## Run the app remotely
You can run the application on a remote PC by simply adding a setting to ssh config.
First, perform the above installation on the remote PC as well.

Replace IP_ADDRESS, USERNAME, KEY, and SHELL with your environment.

```config:~/.ssh/config
Host dev-server
HostName       IP_ADDRESS
Port           22
User           USERNAME
IdentityFile   ~/.ssh/KEY
RequestTTY     force
RemoteCommand  python3 ~/xsprash/xsprash.py server & SHELL
PermitLocalCommand yes
LocalCommand   python3 ~/xsprash/xsprash.py client &
LocalForward   10001 127.0.0.1:10001
```

### Points
- RemoteCommand remotely starts xpra server and waits for it in a shell
- LocalCommand starts the xpra client locally.

Now let's connect to the server from the client.
```
ssh dev-server
```

When the server prompts you,
````
vscode
````
This will run vscode remotely.

When you log out from the remote, you can exit by typing `exit` once in normal ssh, but you need to do `Ctrl+c` again because LocalCommand is still active.

Now you can use vscode running on remote locally.
In this state, the local and remote directories are not shared.
In the following sections, we will explain how to share the persistent data area between local and remote.


## Configure file synchronization
We will use Syncthing's Docker image for file synchronization.
Please change the ssh config setting to the following.

```config:~/.ssh/config
Host dev-server
HostName       IP_ADDRESS
Port           22
User           USERNAME
IdentityFile   ~/.ssh/KEY
RequestTTY     force
RemoteCommand  python3 ~/xsprash/xsprash.py server & python3 ~/xsprash/xsprash.py sync & SHELL
PermitLocalCommand yes
LocalCommand   python3 ~/xsprash/xsprash.py client & python3 ~/xsprash/xsprash.py sync &
LocalForward   10001 127.0.0.1:10001
LocalForward   18384 127.0.0.1:8384
```

You can access the following address in your browser to set up synchronization.
See [Syncthing documentation](https://docs.syncthing.net/) for details.

Local Syncthing: `http://127.0.0.1:8384`

Remote Syncthing: `http://127.0.0.1:18384`

Add the directory you want to share under `xsprash/volume/` and set up the sharing.


## Server-side firewall settings

### When using Syncthing

#### Inbound

- From:Local side Global IP To:Server IP Port:22000/udp
- From:Local side Global IP To:Server IP Port:22000/tcp
- From:Local side Global IP To:Server IP Port:22/tcp

#### Outbound

- From: Server IP To: Any Port: Any

### No file synchronization

#### Inbound

- From:Local side Global IP To:Server IP Port:22/tcp

#### Outbound

- From:Server IP To:Any Port:Any
