# xsprash
A Rootless, Seamless, Stateless Development Environment.

# ローカル環境構築

下記に習って docker rootless をインストール

https://docs.docker.jp/engine/security/rootless.html

bashの場合は、`~/.bash_profile`に下記を追加

```bash:~/.bash_profile
export PATH=$HOME/bin:$PATH
export DOCKER_HOST=unix://$XDG_RUNTIME_DIR/docker.sock
```

fish shellの場合は、
```bash:bash
$ set -U fish_user_paths ~/bin $fish_user_paths
$ set -Ux DOCKER_HOST unix://$XDG_RUNTIME_DIR/docker.sock
```

一旦ログアウトしてログインし直してください。

docker rootlessが動作するか確認。
```bash:bash
$ docker ps
CONTAINER ID  IMAGE  COMMAND  CREATED  STATUS  PORTS  NAMES
```

次に x11docker のインストールをします。
まず、ディストリビューション毎の推奨パッケージをインストール

https://github.com/mviereck/x11docker/wiki/Dependencies#recommended-base

Arch Linux だったら、

```bash:bash
sudo pacman -S xpra xorg-server-xephyr xorg-xinit xorg-xauth xclip xorg-xhost xorg-xrandr xorg-xdpyinfo nxagent glu
```
xpraのGPUサポートのため`glu`もインストールしています。

依存関係のインストールが終わったら x11docker 本体のインストール

```bash:bash
curl -fsSL https://raw.githubusercontent.com/mviereck/x11docker/master/x11docker | sudo bash -s -- --update
```

システム設定
X ServerをX11dockerから起動できるように設定変更。

```bash:bash
echo "allowed_users=anybody" | sudo tee -a /etc/X11/Xwrapper.config
```

コンテナ内からDBUSに接続できるように設定変更。
`/usr/share/dbus-1/session.d/session-local.conf`を作成

```config:/usr/share/dbus-1/session.d/session-local.conf
<!DOCTYPE busconfig PUBLIC "-//freedesktop//DTD D-Bus Bus Configuration 1.0//EN"
 "http://www.freedesktop.org/standards/dbus/1.0/busconfig.dtd">
<busconfig>
  <auth>ANONYMOUS</auth>
  <allow_anonymous/>
</busconfig>
```

xpra イメージと vscode イメージをビルドする

```bash:bash
$ git clone https://github.com/ysuito/xsprash.git
$ docker build -t ubuntubase xsprash/src/ubuntubase_ja/
$ docker build -t xpra xsprash/src/xpra/
$ docker build -t vscode xsprash/src/vscode/
```
`src/`配下には他のアプリケーションの定義もありますが、サンプルたのめ上記のもののみをビルドしています。

イメージがビルド出来たかどうか確認します。

```bash:bash
$ docker images
REPOSITORY                                           TAG               IMAGE ID       CREATED        SIZE
vscode                                               latest            5419f3b23f23   41 hours ago   1.6GB
xpra                                                 latest            dcede0d68d1e   41 hours ago   1.49GB
ubuntu                                               latest            ba6acccedd29   2 months ago   72.8MB
```

アプリが利用するリソースを設定するためのアプリケーション定義をします。
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

gnomeデスクトップアプリとして登録したい場合は、`icon/`に好きなiconファイルを設置し、下記を実行。
```bash:bash
$ python xsprash.py desktop-entry vscode
Icon File:vscode.svg
```
これで、gnomeデスクトップアプリとして利用できるようになります。

コマンドラインから起動したい場合は、下記を実行。
```bash:bash
$ python xsprash.py aliases
alias vscode='python /home/$USER/xsprash/xsprash.py start vscode'
```

alias設定が出力されるので、お使いのシェルのalias設定ファイルに追記してください。

これでコンテナ上に稼働するvscodeが起動します。

```bash:bash
$ vscode
```

vscode Remote Containerで開発する場合は、`devcontainer.json`に下記設定を加えてください。

```json:devcontainer.json
	"remoteUser": "root",
	"workspaceMount": "source=${localEnv:BIND_PATH}/${localWorkspaceFolderBasename},target=/workspace,type=bind,consistency=cached",
	"workspaceFolder": "/workspace"
```

これでローカル側で vscode が起動できるようになりました。

# リモートサーバー構築

ローカル環境構築と同様の作業を実行してください。

加えて`~/.profile`に下記内容を加えてください。
```bash:~/.profile
export PATH=$HOME/bin:$PATH
export DOCKER_HOST=unix://$XDG_RUNTIME_DIR/docker.sock
```

これでリモートサーバの構築は終了です。
リモートサーバがPCが画面やキーボードのある環境なら、`$ vscode`とすれば、ローカルでアプリが立ち上がります。

# SSH設定

IP_ADDRESS,USERNAME,KEY,SHELL の部分は各環境に置き換えてください。

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

ポイント

- RemoteCommand では、リモートで xpra サーバを起動しシェルで待受
- LocalCommand では、ローカルで xpra クライアントを起動

それではクライアントからサーバへ接続します。

```
ssh dev-server
```

サーバのプロンプトが表示されたら

```
vscode
```

※リモートからログアウトする際、普通の ssh なら一度`exit`と打てば抜けられますが、LocalCommand が継続してしまっているので更に`Ctrl+c`をする必要が有ります。

これでリモートで実行している vscode をローカルで利用出来ます。
この状態では、ローカルとリモートのディレクトリは非共有状態です。
以下で、永続データ領域をローカルとリモートで共有する方法を解説していきます。

# Syncthing によるファイル同期設定

syncthing 公式の Docker Image を利用します。ssh config の設定を修正します。

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

ポイント

- RemoteCommand に`docker run -p 8384:8384 -p 22000:22000/tcp -p 22000:22000/udp -v ~/xsprash/volume:/var/syncthing --hostname=dev-server -e PUID=0 -e PGID=0 syncthing/syncthing`を追加してリモートで Syncthing コンテナ起動
- LocalCommand にも`docker run --rm -p 8384:8384/tcp -p 22000:22000/tcp -p 22000:22000/udp -v ~/xsprash/volume:/var/syncthing --hostname=local-pc -e PUID=0 -e PGID=0 docker.io/syncthing/syncthing`を追加してローカルで Syncthing コンテナ起動
- docker rootless はコンテナ内部では root で動作しようとするが、syncthing の docker image は、entrypoint でユーザハンドリングしようとするので、root のままで進むように$PUIDと$PGID を設定している。そうしないとディレクトリの所有者が狂う。
- LocalForward に`18384 127.0.0.1:8384`を設定、リモートの管理用 WebUI にアクセス出来るようにする。ローカルのポートと被るのでずらしている。

ブラウザで下記アドレスにアクセスすると同期設定が出来る。
詳細は Syncthing のドキュメントを参照してください。

https://docs.syncthing.net/

ローカルの Syncthing： `http://127.0.0.1:8384`

リモートの Syncthing： `http://127.0.0.1:18384`

## Syncthing 設定簡易フロー

- 相互にデバイス追加
- `~/xsprash/volume/`配下の共有したいディレクトリを追加して共有設定

経路上の NAT ルータの UPnP を有効にするとダイレクトコネクションになりネットワークが早くなる。
UPnP が無効でも Relay サーバー経由でファイル共有は出来ます。

# SSHFS によるファイル同期設定

この方法はローカル側とリモート側の UID が一致していないとパーミッションがずれて利用できなくなります。

## ローカル側

クライアント側で sshd を稼働させ、ユーザの authorized_keys を追加
セキュリティの心配があれば、

```config:/etc/ssh/sshd_config
ListenAddress 127.0.0.1
ListenAddress ::1
```

を追加して、ssh ログインできる IP をローカルに限定すれば安心。

クライアントの秘密鍵をサーバに運び下記を実行。

## サーバー側

SSHFS をインストールします。

```
sudo apt install sshfs
```

`~/.ssh/config`に下記を追加。LOCALPC,USER,LOCALPCKEY の部分は適宜変更してください。

```config:~/.ssh/config
Host           LOCALPC
HostName       127.0.0.1
Port           2222
User           USER
IdentityFile   ~/.ssh/LOCALPCKEY
```

初めて config ファイルを作成した場合は、下記を実行。

```
chmod 600 ~/.ssh/config
```

一度クライアントに接続して known_hosts に fingerprint を追加しておいてください。

```
ssh LOCALPC
```

## クライアント側

ssh config を修正

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

ポイント

- RemoteForward を追加し、リモートから SSH 出来るように設定
- RemoteCommand に`sshfs LOCALPC:volume ~/volume`を追加
  （マウント時にエラーとなるため、リモート側の`~/volume`配下を消去しておいてください。）


# ファイル同期パターン

- 同期なし（ローカルとリモートが別々）
- SSHFS でローカルディレクトリをリモートにマウント（タイムラグ無、低スループット）
- Syncthing でローカルとリモートのディレクトリを同期（タイムラグ有、高スループット）

# サーバー側ファイアーウォール設定

## Syncthing 利用の場合

### Inbound

- From:ローカル側グローバル IP To:サーバー IP Port:22000/udp
- From:ローカル側グローバル IP To:サーバー IP Port:22000/tcp
- From:ローカル側グローバル IP To:サーバー IP Port:22/tcp

### Outbound

- From:サーバー IP To:Any Port:Any

## SSHFS、ファイル同期しない場合

### Inbound

- From:ローカル側グローバル IP To:サーバー IP Port:22/tcp

### Outbound

- From:サーバー IP To:Any Port:Any

# 環境の切り替え方法

- ssh 接続先のプロンプトでアプリを起動すればリモート環境
- ローカルのターミナルでアプリを起動すればローカル環境
