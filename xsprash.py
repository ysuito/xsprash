#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""xsprash main

* This program provides management functions for GUI applications running on containers.

Todo:
    * launch each X Server per app
    * tighten auth
    * chown
    * build
    * build-all
"""

import argparse
from pathlib import Path
import subprocess
import os
import json
import time

parser = argparse.ArgumentParser(
    description='A program to manage GUI applications running inside containers.')
parser.add_argument('command',
                    choices=[
                        'create', 'start', 'client', 'server',
                        'sync', 'list', 'aliases', 'desktop-entry',
                        'chown', 'build', 'build-all'
                    ],
                    help='command')
parser.add_argument('target', help='command target', nargs='?')

args = parser.parse_args()

HOME = os.environ['HOME']
XSPRASHHOME = os.path.abspath(os.path.dirname(__file__))
SRC_PATH = os.path.join(XSPRASHHOME, 'src/')
LOG_PATH = os.path.join(XSPRASHHOME, 'log/')
VOL_PATH = os.path.join(XSPRASHHOME, 'volume/')
ICON_PATH = os.path.join(XSPRASHHOME, 'icon/')
DESKTOPFILE_DIR = os.path.join(HOME, '.local/share/applications/')

UID = os.getuid()
ENV = os.environ.copy()

DOCKER_EXECUTABLE = os.path.expandvars('$HOME/bin/docker')
os.environ['DOCKER_SOCK'] = os.path.expandvars('$XDG_RUNTIME_DIR/docker.sock')

design_file_path = os.path.join(XSPRASHHOME, 'design.json')


def init():
    """initialize

    initialize

    Args:
        None

    Returns:
        None

    """

    global DOCKER_EXECUTABLE

    setting_file_path = os.path.join(XSPRASHHOME, 'setting.json')
    with open(setting_file_path, 'r', encoding='utf-8') as setting_file:
        setting = json.load(setting_file)
        DOCKER_EXECUTABLE = os.path.expandvars(setting['docker_executable'])
        os.environ['DOCKER_SOCK'] = os.path.expandvars(setting['docker_sock'])


def read_design():
    """read app design

    read app design

    Args:
        None

    Returns:
        Dictionary: apps design

    """
    with open(design_file_path, 'r', encoding='utf-8') as design_file:
        design = json.load(design_file)
        return design


def save_design(design):
    """save app design

    save app design

    Args:
        design (Dictionary): apps design to save

    Returns:
        None

    """
    with open(design_file_path, 'w', encoding='utf-8') as design_file:
        json.dump(design, design_file)


def exec_with_logging(app_name, command, side):
    """exec app

    exec app

    Args:
        app_name (String): app name
        command (List<String>): exec commands
        side (String): local or remote

    Returns:
        None

    """
    logfile_path = os.path.join(LOG_PATH, app_name + f'_{side}.log')
    with open(logfile_path, 'w', encoding='utf-8') as logfile:
        subprocess.Popen(
            command, env=ENV, universal_newlines=True, stdout=subprocess.DEVNULL, stderr=logfile)


def create():
    """create app design

    create app design with dialog, then save to design.json

    Args:
        None

    Returns:
        None

    """

    app_name = input('App Name(String):')
    image = input('Image(String):')
    command = input('Command(String):')
    audio = bool(input('Audio(y/N):') == 'y')
    input_method = bool(input('Input Method(y/N):') == 'y')
    volume = bool(input('Volume(y/N):') == 'y')
    docker_sock = bool(input('Share Docker Socket(y/N):') == 'y')
    tmpfs = bool(input('Share tmpfs /dev/shm(y/N):') == 'y')
    gpu = bool(input('Share gpu /dev/dri(y/N):') == 'y')
    kvm = bool(input('Share kvm /dev/kvm(y/N):') == 'y')
    privileged = bool(input('Privileged(y/N):') == 'y')
    options = input('Docker Options(String):')
    if len(options) > 0:
        options = options.split(" ")
    else:
        options = []
    app_design = {
        "app_name": app_name,
        "image": image,
        "command": command,
        "audio": audio,
        "input_method": input_method,
        "volume": volume,
        "docker_sock": docker_sock,
        "tmpfs": tmpfs,
        "gpu": gpu,
        "kvm": kvm,
        "privileged": privileged,
        "options": options
    }
    design = read_design()
    design[app_name] = app_design
    save_design(design)


def docker_command_constructor(app_design, display):
    """generate docker command

    generate docker command from app design

    Args:
        app_design (Dictionary): app design to generate options
        display (int): xpra display number

    Returns:
        None

    """

    command = ["docker", "run"]
    command.extend(["--rm", "-t", "--net=bridge", "--shm-size=4096m"])
    command.extend(['--name', app_design["app_name"]])
    command.extend(["--env", f"DISPLAY=:{display}"])
    command.append(
        f"--volume=/tmp/.X11-unix/X{display}:/tmp/.X11-unix/X{display}")
    image_command = 'groupadd -g 1000 user && '
    if app_design.get("volume"):
        app_vol = os.path.join(VOL_PATH, app_design["app_name"])
        if not Path(app_vol).is_dir():
            os.makedirs(app_vol)
        command.append(f"--volume={app_vol}:/home/user")
        image_command += 'useradd -u 1000 -g user user && chown -R user:user /home/user; '
    else:
        image_command += 'useradd -m -u 1000 -g user user && chown -R user:user /home/user; '
    if app_design.get("audio"):
        if display == 0:
            command.extend([
                "--env", "PULSE_COOKIE=/tmp/pulse/cookie",
                "--env", "PULSE_SERVER=unix:/tmp/pulse/native",
                f"--volume=/run/user/{UID}/pulse/native:/tmp/pulse/native",
                f"--volume={ENV['HOME']}/.config/pulse/cookie:/tmp/pulse/cookie_org:ro"
            ])
        else:
            command.extend([
                "--env", "PULSE_COOKIE=/tmp/pulse/cookie",
                "--env", "PULSE_SERVER=unix:/tmp/pulse/native",
                f"--volume=/run/user/{UID}/xpra/pulse-{display}/pulse/native:/tmp/pulse/native",
                f"--volume={ENV['HOME']}/.config/pulse/cookie:/tmp/pulse/cookie_org:ro"
            ])
        image_command += 'cp /tmp/pulse/cookie_org /tmp/pulse/cookie; chmod 644 /tmp/pulse/cookie;'
    if app_design.get("input_method"):
        if 'GTK_IM_MODULE' in ENV:
            command.extend([
                "--env", f"GTK_IM_MODULE={ENV['GTK_IM_MODULE']}"
            ])
        if 'XMODIFIERS' in ENV:
            command.extend([
                "--env", f"XMODIFIERS={ENV['XMODIFIERS']}"
            ])
        if 'QT_IM_MODULE' in ENV:
            command.extend([
                "--env", f"QT_IM_MODULE={ENV['QT_IM_MODULE']}"
            ])
        command.extend([
            "--env", f"DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{UID}/bus",
            f"--volume=/run/user/{UID}/bus:/run/user/{UID}/bus"
        ])
    if app_design.get("docker_sock"):
        app_bind_path = f"BIND_PATH={os.path.join(VOL_PATH, app_design['app_name'])}"
        command.extend(["--env", app_bind_path])
        command.append(
            f"--volume=/run/user/{UID}/docker.sock:/var/run/docker.sock")
        image_command += 'usermod -aG root,docker user;'
    if app_design.get("tmpfs"):
        command.extend(["--tmpfs", "/dev/shm"])
    if app_design.get("gpu"):
        command.append("--device=/dev/dri:/dev/dri")
    if app_design.get("kvm"):
        command.append("--device=/dev/kvm:/dev/kvm")
    if app_design.get("privileged"):
        command.append("--privileged")
    if app_design.get("options"):
        command.extend(app_design["options"])
    image_command += f'su user -c "{app_design["command"]}"'
    command.extend([app_design["image"], "bash", "-c", image_command])
    return command


def start(app_name):
    """start local app

    start local app based on app design

    Args:
        app_name (String): app name to get app design

    Returns:
        None

    """
    design = read_design()
    if app_name not in design:
        print('App design not found. Create app design.')
        return
    app_design = design[app_name]

    if 'SSH_CONNECTION' in ENV:
        display = 101
    else:
        display = 0
        exec_with_logging(
            'Xserver_chmod',
            ['bash', '-c', 'DISPLAY=:0; chmod 777 /tmp/.X11-unix/X0 && xhost +local:'],
            'local')
    command = docker_command_constructor(app_design, display)

    exec_with_logging(app_name, command, 'local')


def client():
    """launch xpra client to connect xpra server

    launch xpra client to connect xpra server

    Args:
        None

    Returns:
        None

    """

    # Wait for the server to start.
    time.sleep(2)

    port = 10001
    display = 101
    command = ['x11docker', '--gpu', '-c', '--exe', 'xpra',
               'attach', f'tcp://127.0.0.1:{port}/{display}']

    exec_with_logging('xpra_client', command, 'local')


def server():
    """launch xpra server

    launch xpra server

    Args:
        None

    Returns:
        None

    """
    port = 10001
    display = 101

    command = ['xpra', 'start', f':{display}', f'--bind-tcp=127.0.0.1:{port}',
               '--start=xhost +local:']

    exec_with_logging('xpra_server', command, 'remote')


def syncthing():
    """launch syncthing

    launch syncthing

    Args:
        None

    Returns:
        None

    """
    if 'SSH_CONNECTION' in ENV:
        hostname = 'remote'
    else:
        hostname = 'local'
    command = ['docker', 'run', '--rm', '-t']
    command.extend(['--name', 'syncthing'])
    command.extend(
        ['-p127.0.0.1:8384:8384', '-p22000:22000/tcp', '-p22000:22000/udp'])
    command.extend([f'--volume={VOL_PATH}:/var/syncthing'])
    command.extend([f'--hostname={hostname}'])
    command.extend(['--env', 'PUID=0', '--env', 'PGUID=0'])
    command.extend(['syncthing/syncthing'])

    exec_with_logging('syncthing', command, 'local')


def app_list():
    """list apps

    list apps

    Args:
        None

    Returns:
        None

    """
    design = read_design()
    for app_name in design.keys():
        print(app_name)


def generate_desktop_entry(app_name):
    """add desktop entry

    add desktop entry

    Args:
        app_name (String): app name to entry

    Returns:
        None

    """
    design = read_design()
    if app_name not in design:
        print('App design not found. Create app design.')
        return
    icon_file = input('Icon File:')
    entry = (
        "[Desktop Entry]\n"
        "Type=Application\n"
        f"Name={app_name}\n"
        "MimeType=application/vnd.ms-htmlhelp;\n"
        f"Path={XSPRASHHOME}\n"
        f"Exec=bash -c \"python3 xsprash.py start {app_name}\"\n"
        "NoDisplay=false\n"
        "Terminal=false\n"
        "StartupNotify=true\n"
        "Categories=Development;\n"
        f"Icon={os.path.join(ICON_PATH, icon_file)}\n"
    )
    entry_file = os.path.join(DESKTOPFILE_DIR, f'{app_name}.desktop')
    with open(entry_file, 'w', encoding='utf-8') as entryfile:
        entryfile.write(entry)
    command = ['update-desktop-database', DESKTOPFILE_DIR]
    subprocess.call(command)


def generate_aliases():
    """print designs for aliases

    print designs for aliases

    Args:
        None

    Returns:
        None

    """
    design = read_design()
    for app_name, conf in design.items():
        if conf['image'].startswith('ubuntubase'):
            continue
        print(
            f"alias {app_name}='python3 {os.path.join(XSPRASHHOME, 'xsprash.py')} start {app_name}'")


def chown(app_name):
    """change volume owner to host user

    change volume owner to host user

    Args:
        app_name (String): app name to change ownership

    Returns:
        None

    """


def build(app_name):
    """build app image

    build app image

    Args:
        app_name (String): app name to build

    Returns:
        None

    """


def build_all():
    """build all app image

    build all app image

    Args:
        None

    Returns:
        None

    """


def main():
    """main

    main

    Args:
        None

    Returns:
        None

    """
    init()
    if args.command == 'start':
        start(args.target)
    elif args.command == 'create':
        create()
    elif args.command == 'client':
        client()
    elif args.command == 'server':
        server()
    elif args.command == 'sync':
        syncthing()
    elif args.command == 'list':
        app_list()
    elif args.command == 'aliases':
        generate_aliases()
    elif args.command == 'desktop-entry':
        generate_desktop_entry(args.target)
    elif args.command == 'chown':
        chown(args.target)
    elif args.command == 'build':
        build(args.target)
    elif args.command == 'build-all':
        build_all()


if __name__ == "__main__":
    main()
