# xsprash
A Rootless, Seamless, Stateless Development Environment on Linux.

## Supported System
xsprashはLinux上で稼働します。

## 特徴
GUIアプリをLinuxコンテナ上で動かすことを可能にします。
画面表示、音声出力、インプットメソッドに対応しています。

### Rootless
すべてのコンテナはRootlessモードで動くので、構築後は一度もroot権限を必要としません。
各コンテナのホームディレクトリはホストの一箇所にバインドされるので、ホスト環境をいつまでもきれいなままに保ちます。

### Seamless
sshで接続して、アプリを起動するだけで、別のPCやサーバー上で実行するアプリをローカルで表示することができます。
ラップトップで高付加の処理をいともかんたんに実行します。

### Stateless
バインドされたホームディレクトリ以外はアプリ終了時にすべて破棄されるので、環境の再現性が高くなります。
別のPCに非常に簡単に引っ越せます。

## Installation
### Docker Rootless(Client and Server)
[Run the Docker daemon as a non-root user](https://docs.docker.com/engine/security/rootless/) に従って docker rootless をインストール

### x11docker(Only Client)
x11dockerのための依存パッケージを[recommended-base](https://github.com/mviereck/x11docker/wiki/Dependencies#recommended-base)に従ってインストール

x11docker本体のインストール
```bash:bash
curl -fsSL https://raw.githubusercontent.com/mviereck/x11docker/master/x11docker | sudo bash -s -- --update
```

### システム設定(Only Client)
X ServerをX11dockerから起動できるように設定変更。
`/etc/X11/Xwrapper.config`を編集
```config:/etc/X11/Xwrapper.config
...
allowed_users=anybody
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

### イメージビルド(Client and Server)

vscode イメージをビルドする

```bash:bash
git clone https://github.com/ysuito/xsprash.git
cd xsprash
docker build -t ubuntubase src/ubuntubase/
docker build -t vscode src/vscode/
```
日本語環境の場合は、`ubuntubase`を`ubuntubase_ja`に変更してください。
`src/`配下には他のアプリケーションの定義もありますが、サンプルのため上記のもののみをビルドしています。

### アプリ定義(Client and Server)

アプリが利用するリソースを設定するためのアプリケーション定義をします。
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

gnomeデスクトップアプリとして登録したい場合は、`icon/`に好きなiconファイルを設置し、下記を実行。
```bash:bash
$ python3 xsprash.py desktop-entry vscode
Icon File:vscode.svg
```
これで、gnomeデスクトップアプリとして利用できるようになります。

コマンドラインから起動したい場合は、下記を実行。
```bash:bash
$ python3 xsprash.py aliases
alias vscode='python3 /home/$USER/xsprash/xsprash.py start vscode'
```

alias設定が出力されるので、お使いのシェルのalias設定ファイルに追記してください。

これでコンテナ上で稼働するvscodeが起動します。

```bash:bash
vscode
```

vscode Remote Containerで開発する場合は、`devcontainer.json`に下記設定を加えてください。

```json:devcontainer.json
	"remoteUser": "vscode",
	"workspaceMount": "source=${localEnv:BIND_PATH}/${localWorkspaceFolderBasename},target=/workspace,type=bind,consistency=cached",
	"workspaceFolder": "/workspace"
```

## リモートでアプリ実行(Client)
ssh configに設定を加えるだけで、リモートにあるPCでアプリを実行できるようになります。
まず、リモート側のPCでも上記内容のインストールを実行してください。

IP_ADDRESS,USERNAME,KEY,SHELL の部分は各環境に置き換えてください。

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

### ポイント
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


## ファイル同期設定
SyncthingのDocker イメージを利用してファイル動機をします。
ssh configの設定を下記内容に変更してください。

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

ブラウザで下記アドレスにアクセスすると同期設定が出来る。
詳細は [Syncthing のドキュメント](https://docs.syncthing.net/)を参照してください。

ローカルの Syncthing： `http://127.0.0.1:8384`

リモートの Syncthing： `http://127.0.0.1:18384`

`xsprash/volume/`配下の共有したいディレクトリを追加して共有設定してください。


## サーバー側ファイアーウォール設定

### Syncthing 利用の場合

#### Inbound

- From:ローカル側グローバル IP To:サーバー IP Port:22000/udp
- From:ローカル側グローバル IP To:サーバー IP Port:22000/tcp
- From:ローカル側グローバル IP To:サーバー IP Port:22/tcp

#### Outbound

- From:サーバー IP To:Any Port:Any

### ファイル同期しない場合

#### Inbound

- From:ローカル側グローバル IP To:サーバー IP Port:22/tcp

#### Outbound

- From:サーバー IP To:Any Port:Any

## 環境の切り替え方法

- ssh 接続先のプロンプトでアプリを起動すればリモート環境
- ローカルのターミナルでアプリを起動すればローカル環境
