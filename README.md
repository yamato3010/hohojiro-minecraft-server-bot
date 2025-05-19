# Hohojiro Minecraft Server Bot

このプロジェクトは、Discordを通じてAzure上のMinecraftサーバーを管理するためのボットです。  
ボットを使用して、Minecraftサーバーの起動、停止、状態確認などを簡単に行うことができます。

## 機能

- **Minecraftサーバーの起動**: `/vmstart`
- **Minecraftサーバーの停止**: `/vmstop`
- **利用可能なVMの一覧表示**: `/vmlist`
- **VMの状態確認**: `/vmstatus`
- **ヘルプコマンド**: `/vmhelp`

## 必要な環境変数

ボットを動作させるには、以下の環境変数を`.env`ファイルに設定する必要があります。

```env
DISCORD_TOKEN=YOUR_DISCORD_BOT_TOKEN
AZURE_TENANT_ID=YOUR_AZURE_TENANT_ID
AZURE_CLIENT_ID=YOUR_AZURE_CLIENT_ID
AZURE_CLIENT_SECRET=YOUR_AZURE_CLIENT_SECRET
AZURE_SUBSCRIPTION_ID=YOUR_AZURE_SUBSCRIPTION_ID
DEFAULT_RESOURCE_GROUP=YOUR_DEFAULT_RESOURCE_GROUP
DEFAULT_VM_NAME=YOUR_DEFAULT_VM_NAME
```

- **DISCORD_TOKEN**: Discordボットのトークン。
- **AZURE_TENANT_ID**: AzureのテナントID。
- **AZURE_CLIENT_ID**: AzureのクライアントID。
- **AZURE_CLIENT_SECRET**: Azureのクライアントシークレット。
- **AZURE_SUBSCRIPTION_ID**: AzureのサブスクリプションID。
- **DEFAULT_RESOURCE_GROUP**: デフォルトのリソースグループ名。
- **DEFAULT_VM_NAME**: デフォルトのVM名。

## 必要な依存関係

以下のPythonライブラリが必要です。`requirements.txt`に記載されています。

- `discord.py==2.1.1`
- `Flask==2.2.3`
- `azure-identity`
- `azure-mgmt-compute`

依存関係をインストールするには、以下のコマンドを実行してください。

```bash
pip install -r requirements.txt
```

## 使用方法

1. `.env`ファイルを作成し、必要な環境変数を設定します。
2. 以下のコマンドでボットを起動します。

```bash
python main.py
```

3. Discordサーバーにボットを招待し、以下のコマンドを使用して操作します。

### 主なコマンド

- `/vmstart`: デフォルトのMinecraftサーバーを起動します。
- `/vmstop`: デフォルトのMinecraftサーバーを停止します。
- `/vmlist`: 利用可能なVMの一覧を表示します。
- `/vmstatus`: 指定したVMの状態を確認します。
- `/vmhelp`: 利用可能なコマンドの一覧を表示します。

## Dockerでの実行

このプロジェクトはDockerを使用して実行することもできます。

1. Dockerイメージをビルドします。

```bash
docker build -t hohojiro-minecraft-bot .
```

2. コンテナを起動します。

```bash
docker run --env-file .env hohojiro-minecraft-bot
```

## 注意事項

- Azureの認証情報が正しく設定されていない場合、VM操作機能が正しく動作しない可能性があります。
- Discordボットのトークンは機密情報です。第三者に漏れないように注意してください。

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。
