import os
import discord
from discord.ext import commands
from azure.identity import ClientSecretCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from keep_alive import keep_alive
import logging

# ロギングの設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('azure_vm_bot')

# 環境変数から設定を取得
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
AZURE_TENANT_ID = os.getenv('AZURE_TENANT_ID')
AZURE_CLIENT_ID = os.getenv('AZURE_CLIENT_ID')
AZURE_CLIENT_SECRET = os.getenv('AZURE_CLIENT_SECRET')
AZURE_SUBSCRIPTION_ID = os.getenv('AZURE_SUBSCRIPTION_ID')

# デフォルトのVM設定
DEFAULT_RESOURCE_GROUP = os.getenv('DEFAULT_RESOURCE_GROUP')
DEFAULT_VM_NAME = os.getenv('DEFAULT_VM_NAME')

# Discordボットの設定
intents = discord.Intents.default()
intents.message_content = True  # 必要に応じてコメント解除
bot = commands.Bot(command_prefix='/', intents=intents)

# Azure認証
try:
    credential = ClientSecretCredential(
        tenant_id=AZURE_TENANT_ID,
        client_id=AZURE_CLIENT_ID,
        client_secret=AZURE_CLIENT_SECRET
    )

    # Azure Compute クライアント
    compute_client = ComputeManagementClient(
        credential=credential,
        subscription_id=AZURE_SUBSCRIPTION_ID
    )
    logger.info("Azure認証が成功しました")
except Exception as e:
    logger.error(f"Azure認証中にエラーが発生しました: {str(e)}")
    compute_client = None

@bot.event
async def on_ready():
    logger.info(f'{bot.user} としてログインしました')
    logger.info(f'Bot ID: {bot.user.id}')
    logger.info(f'接続サーバー数: {len(bot.guilds)}')
    logger.info('------')

@bot.event
async def on_message(message):
    # 自分自身のメッセージには反応しない
    if message.author == bot.user:
        return
    
    logger.info(f'メッセージ受信: {message.content} from {message.author}')
    
    # コマンド処理を続行
    await bot.process_commands(message)

@bot.command(name='ping')
async def ping(ctx):
    """ボットが応答するかテストします"""
    logger.info(f'pingコマンドを受信: {ctx.author}')
    await ctx.send('Pong! Botは正常に動作しています。')

@bot.command(name='vmlist')
async def vm_list(ctx):
    """利用可能なVMの一覧を表示します"""
    try:
        vms = compute_client.virtual_machines.list_all()
        vm_list = []
        
        for vm in vms:
            resource_group = vm.id.split('/')[4]  # リソースグループ名を取得
            vm_status = compute_client.virtual_machines.instance_view(
                resource_group_name=resource_group,
                vm_name=vm.name
            )
            
            # VMの電源状態を取得
            power_state = "不明"
            for status in vm_status.statuses:
                if status.code.startswith('PowerState'):
                    power_state = status.display_status
            
            vm_list.append(f"名前: {vm.name}, リソースグループ: {resource_group}, 状態: {power_state}")
        
        if vm_list:
            response = "**利用可能なVMの一覧:**\n" + "\n".join(vm_list)
        else:
            response = "利用可能なVMが見つかりませんでした。"
        
        await ctx.send(response)
    except Exception as e:
        await ctx.send(f"エラーが発生しました: {str(e)}")

@bot.command(name='vmstart')
async def vm_start(ctx, resource_group: str = None, vm_name: str = None):
    """VMを起動します
    
    引数:
    resource_group -- VMのリソースグループ名
    vm_name -- VM名
    """

    # デフォルト値を使用
    resource_group = resource_group or DEFAULT_RESOURCE_GROUP
    vm_name = vm_name or DEFAULT_VM_NAME
    
    # パラメータチェック
    if not resource_group or not vm_name:
        missing_params = []
        if not resource_group:
            missing_params.append("DEFAULT_RESOURCE_GROUP")
        if not vm_name:
            missing_params.append("DEFAULT_VM_NAME")
        
        await ctx.send(f"エラー: 必要なパラメータが不足しています。.envファイルに{', '.join(missing_params)}を設定してください。")
        return

    try:
        await ctx.send(f"▶️{vm_name} の起動を開始します。しばらくお待ちください...")
        
        async_vm_start = compute_client.virtual_machines.begin_start(
            resource_group_name=resource_group,
            vm_name=vm_name
        )
        async_vm_start.wait()

        # 起動後にパブリックIPを取得
        network_client = NetworkManagementClient(credential, AZURE_SUBSCRIPTION_ID)
        nic_id = compute_client.virtual_machines.get(
            resource_group_name=resource_group,
            vm_name=vm_name
        ).network_profile.network_interfaces[0].id
        
        nic_name = nic_id.split('/')[-1]
        nic_resource_group = nic_id.split('/')[4]
        public_ip_id = network_client.network_interfaces.get(
            resource_group_name=nic_resource_group,
            network_interface_name=nic_name
        ).ip_configurations[0].public_ip_address.id
        
        public_ip_name = public_ip_id.split('/')[-1]
        public_ip = network_client.public_ip_addresses.get(
            resource_group_name=nic_resource_group,
            public_ip_address_name=public_ip_name
        ).ip_address
        
        await ctx.send(f"✅{vm_name} の起動が完了しました！\nサーバーアドレス: `{public_ip}`")
    except Exception as e:
        await ctx.send(f"❌VMの起動中にエラーが発生しました: {str(e)}")

@bot.command(name='vmstop')
async def vm_stop(ctx, resource_group: str = None, vm_name: str = None):
    """VMを停止します（割り当て解除）
    
    引数:
    resource_group -- VMのリソースグループ名
    vm_name -- VM名
    """
    # デフォルト値を使用
    resource_group = resource_group or DEFAULT_RESOURCE_GROUP
    vm_name = vm_name or DEFAULT_VM_NAME

    # パラメータチェック
    if not resource_group or not vm_name:
        missing_params = []
        if not resource_group:
            missing_params.append("DEFAULT_RESOURCE_GROUP")
        if not vm_name:
            missing_params.append("DEFAULT_VM_NAME")
        
        await ctx.send(f"エラー: 必要なパラメータが不足しています。.envファイルに{', '.join(missing_params)}を設定してください。")
        return

    try:
        await ctx.send(f"⏸️{vm_name} の停止を開始します。しばらくお待ちください...")
        
        # 割り当て解除モードで停止（コスト削減）
        async_vm_deallocate = compute_client.virtual_machines.begin_deallocate(
            resource_group_name=resource_group,
            vm_name=vm_name
        )
        async_vm_deallocate.wait()
        
        await ctx.send(f"✅{vm_name} の停止が完了しました！")
    except Exception as e:
        await ctx.send(f"❌VMの停止中にエラーが発生しました: {str(e)}")

@bot.command(name='vmstatus')
async def vm_status(ctx, resource_group: str = None, vm_name: str = None):
    """VMの現在の状態を確認します
    
    引数:
    resource_group -- VMのリソースグループ名
    vm_name -- VM名
    """
    try:
        vm_status = compute_client.virtual_machines.instance_view(
            resource_group_name=resource_group,
            vm_name=vm_name
        )
        
        # 電源状態を取得
        power_state = "不明"
        for status in vm_status.statuses:
            if status.code.startswith('PowerState'):
                power_state = status.display_status
        
        await ctx.send(f"VM名: {vm_name}\nリソースグループ: {resource_group}\n状態: {power_state}")
    except Exception as e:
        await ctx.send(f"VMの状態確認中にエラーが発生しました: {str(e)}")

@bot.command(name='vmhelp')
async def vm_help_command(ctx):
    """利用可能なコマンドの一覧と使い方を表示します"""
    help_text = """
**ホホジロ用Miencraftサーバー管理ボットのコマンド一覧**

**これだけ覚えればおk！**
`/vmstart` - Minecraftサーバーを起動します
`/vmstop` - Minecraftサーバーを停止します

**管理者向けコマンド**
`/vmlist` - 利用可能なVMの一覧を表示します

`/vmstart リソースグループ名 VM名` - 指定したVM（Minecraftサーバー）を起動します
例: `/vmstart my-resource-group my-vm-name`
`/vmstart` - これだけでもOK！（デフォルトのVM名とリソースグループ名を使用）

`/vmstop リソースグループ名 VM名` - 指定したVM（Minecraftサーバー）を停止します（割り当て解除）
例: `/vmstop my-resource-group my-vm-name`
`/vmstop` - これだけでもOK！（デフォルトのVM名とリソースグループ名を使用）

`/vmstatus リソースグループ名 VM名` - 指定したVMの現在の状態を確認します
例: `/vmstatus my-resource-group my-vm-name`
"""
    await ctx.send(help_text)

# ボットを実行
if __name__ == '__main__':
    try:
        logger.info("ボットの起動を開始します...")
        # message_contentインテントの状態をログに記録
        logger.info(f"message_contentインテント: {'有効' if intents.message_content else '無効'}")
        
        # Bot実行時に環境変数が設定されているか確認
        if not DISCORD_TOKEN:
            logger.error("DISCORD_TOKENが設定されていません。環境変数を確認してください。")
            exit(1)
            
        if not all([AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_SUBSCRIPTION_ID]):
            logger.warning("一部のAzure環境変数が設定されていないため、VM操作機能が制限される可能性があります。")
            
        keep_alive()
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        logger.error(f"ボット実行中にエラー発生: {str(e)}")