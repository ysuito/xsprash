#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""xsprash main

* This program provides management functions for GUI applications running on containers.

Todo:
    * remote_start can't get Dockerfile CMD Values
    * run app as non root user in Docker rootless
    * run chrome without --no-sandbox option
    * launch each X Server per app
"""

import argparse
from pathlib import Path
import subprocess
import os
import json

parser = argparse.ArgumentParser(
    description='A program to manage GUI applications running inside containers.')
parser.add_argument('command', choices=[
                    'create', 'start', 'client', 'server', 'list', 'aliases', 'desktop-entry'
                    ], help='command')
parser.add_argument('app_name', help='app name', nargs='?')

args = parser.parse_args()

home = os.environ['HOME']
xsprashhome = os.path.abspath(os.path.dirname(__file__))
src_path = os.path.join(xsprashhome, 'src/')
log_path = os.path.join(xsprashhome, 'log/')
vol_path = os.path.join(xsprashhome, 'volume/')
icon_path = os.path.join(xsprashhome, 'icon/')
desktopfile_dir = os.path.join(home, '.local/share/applications/')

uid = os.getuid()
env = os.environ.copy()

setting_file_path = os.path.join(xsprashhome, 'setting.json')


def read_definition():
    """read app definition

    read app definition

    Args:
        None

    Returns:
        Dictionary: apps definition

    """
    with open(setting_file_path, 'r', encoding='utf-8') as setting_file:
        setting = json.load(setting_file)
        return setting


def save_definition(setting):
    """save app definition

    save app definition

    Args:
        setting (Dictionary): apps definition to save

    Returns:
        None

    """
    with open(setting_file_path, 'w', encoding='utf-8') as setting_file:
        json.dump(setting, setting_file)


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
    logfile_path = os.path.join(log_path, app_name + f'_{side}.log')
    with open(logfile_path, 'w', encoding='utf-8') as logfile:
        subprocess.Popen(
            command, env=env, universal_newlines=True, stdout=logfile, stderr=logfile)


def create():
    """create app definition

    create app definition with dialog, then save to setting.json

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
    options = input('Docker Options(String):')
    if len(options) > 0:
        options = options.split(" ")
    else:
        options = []
    app_setting = {
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
        "options": options
    }
    setting = read_definition()
    setting[app_name] = app_setting
    save_definition(setting)


def docker_options(app_setting):
    """generate docker options

    generate docker options from app setting

    Args:
        app_setting (Dictionary): app setting to generate options

    Returns:
        None

    """

    options = []

    options.extend(["--rm", "-t", "--net=bridge", "--shm-size=4096m"])

    if app_setting.get("audio"):
        options.extend([
            "--env", f"PULSE_COOKIE=/run/user/{uid}/pulse/cookie",
            "--env", f"PULSE_SERVER=unix:/run/user/{uid}/pulse/native",
            f"--volume=/run/user/{uid}/pulse/native:/run/user/{uid}/pulse/native",
            f"--volume={env['HOME']}/.config/pulse/cookie:/run/user/{uid}/pulse/cookie:ro"
        ])
    if app_setting.get("input_method"):
        options.extend([
            "--env", f"GTK_IM_MODULE={env['GTK_IM_MODULE']}",
            "--env", f"XMODIFIERS={env['XMODIFIERS']}",
            "--env", f"QT_IM_MODULE={env['QT_IM_MODULE']}",
            "--env", f"DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{uid}/bus",
            f"--volume=/run/user/{uid}/bus:/run/user/{uid}/bus"
        ])
    if app_setting.get("volume"):
        app_vol = os.path.join(vol_path, app_setting["app_name"])
        if not Path(app_vol).is_dir():
            os.makedirs(app_vol)
        options.append(f"--volume={app_vol}:/root")
    if app_setting.get("docker_sock"):
        app_bind_path = f"BIND_PATH={os.path.join(vol_path, app_setting['app_name'])}"
        options.extend(
            ["--env", app_bind_path])
        options.append(
            f"--volume=/run/user/{uid}/docker.sock:/var/run/docker.sock")
    if app_setting.get("tmpfs"):
        options.extend(["--tmpfs", "/dev/shm"])
    if app_setting.get("gpu"):
        options.append("--device=/dev/dri:/dev/dri")
    if app_setting.get("kvm"):
        options.append("--device=/dev/kvm:/dev/kvm")
    if app_setting.get("options"):
        options.extend(app_setting["options"])
    return options


def start(app_name):
    """start local app

    start local app based on app definition

    Args:
        app_name (String): app name to get app definition

    Returns:
        None

    """
    setting = read_definition()
    if app_name not in setting:
        print('App setting not found. Create app setting.')
        return
    app_setting = setting[app_name]

    docker_command = ["docker", "run"]
    docker_command.extend(['--name', app_name])
    docker_command.extend(["--volume=/tmp/.X11-unix/X0:/tmp/.X11-unix/X0"])
    docker_command.extend(["--env", "DISPLAY=:0"])

    image_command = [app_setting["image"]]
    image_command.extend(app_setting["command"].split(" "))

    command = []
    command.extend(docker_command)
    command.extend(docker_options(app_setting))
    command.extend(image_command)
    exec_with_logging(app_name, command, 'local')


def remote_start(app_name):
    """start local app

    start local app based on app definition

    Args:
        app_name (String): app name to get app definition

    Returns:
        None

    """
    setting = read_definition()
    if app_name not in setting:
        print('App setting not found. Create app setting.')
        return
    app_setting = setting[app_name]
    docker_command = ['docker', 'run']
    docker_command.extend(['--name', app_name])
    docker_command.extend(['--volumes-from', 'xpra', '-e', 'DISPLAY=:80'])

    image_command = [app_setting["image"]]
    image_command.extend(app_setting["command"].split(" "))

    command = []
    command.extend(docker_command)
    command.extend(docker_options(app_setting))
    command.extend(image_command)
    exec_with_logging(app_name, command, 'remote')


def client():
    """launch xpra client to connect xpra server

    launch xpra client to connect xpra server

    Args:
        None

    Returns:
        None

    """
    command = ['x11docker', '--gpu', '-c', '--exe', 'xpra',
               'attach', 'tcp://127.0.0.1:10000/80']
    exec_with_logging('xpra', command, 'local')


def server():
    """launch xpra server

    launch xpra server

    Args:
        None

    Returns:
        None

    """
    command = ['docker', 'run', '--rm', '-t']
    command.extend(['--name', 'xpra', '-p', '127.0.0.1:10000:10000'])
    command.extend(['--device=/dev/dri:/dev/dri', 'xpra', 'server'])
    exec_with_logging('xpra', command, 'remote')


def app_list():
    """list apps

    list apps

    Args:
        None

    Returns:
        None

    """
    setting = read_definition()
    for app_name in setting.keys():
        print(app_name)


def generate_desktop_entry(app_name):
    """add desktop entry

    add desktop entry

    Args:
        app_name (String): app name to entry

    Returns:
        None

    """
    setting = read_definition()
    if app_name not in setting:
        print('App setting not found. Create app setting.')
        return
    icon_file = input('Icon File:')
    entry = (
        "[Desktop Entry]\n"
        "Type=Application\n"
        f"Name={app_name}\n"
        "MimeType=application/vnd.ms-htmlhelp;\n"
        f"Path={xsprashhome}\n"
        f"Exec=bash -c \"python xsprash.py start {app_name}\"\n"
        "NoDisplay=false\n"
        "Terminal=false\n"
        "StartupNotify=true\n"
        "Categories=Development;\n"
        f"Icon={os.path.join(icon_path, icon_file)}\n"
    )
    entry_file = os.path.join(desktopfile_dir, f'{app_name}.desktop')
    with open(entry_file, 'w', encoding='utf-8') as entryfile:
        entryfile.write(entry)
    command = ['update-desktop-database', desktopfile_dir]
    subprocess.call(command)


def generate_aliases():
    """print settings for aliases

    print settings for aliases

    Args:
        None

    Returns:
        None

    """
    setting = read_definition()
    for app_name, conf in setting.items():
        if conf['image'].startswith('ubuntubase'):
            continue
        print(
            f"alias {app_name}='python {os.path.join(xsprashhome, 'xsprash.py')} start {app_name}'")


def main():
    """main

    main

    Args:
        None

    Returns:
        None

    """
    if args.command == 'start':
        if 'SSH_CONNECTION' in env:
            remote_start(args.app_name)
        else:
            start(args.app_name)
    elif args.command == 'create':
        create()
    elif args.command == 'client':
        client()
    elif args.command == 'server':
        server()
    elif args.command == 'list':
        app_list()
    elif args.command == 'aliases':
        generate_aliases()
    elif args.command == 'desktop-entry':
        generate_desktop_entry(args.app_name)


if __name__ == "__main__":
    main()
