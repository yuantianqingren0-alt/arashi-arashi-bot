import discord
from discord.ext import commands
from discord import app_commands
import os
import asyncio
from datetime import timedelta
from keep_alive import keep_alive

keep_alive()

intents = discord.Intents.default()


class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents
        )

    async def setup_hook(self):
        await self.tree.sync()
        print("スラッシュコマンドの同期が完了しました。")


bot = MyBot()


# ==================================================
# パネル機能（ボタン処理）
# ==================================================

class MultiView(discord.ui.View):

    def __init__(self, custom_message: str, enable_poll: bool):
        super().__init__(timeout=None)
        self.custom_message = custom_message
        self.enable_poll = enable_poll

    @discord.ui.button(
        label="🚀 メッセージ送信",
        style=discord.ButtonStyle.primary
    )
    async def start_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        # 1. タイムアウト防止の応答
        await interaction.response.defer(ephemeral=True)

        # 2. 指定メッセージの5連投
        async def send_fast():
            await interaction.followup.send(
                self.custom_message,
                ephemeral=False
            )

        msg_tasks = [asyncio.create_task(send_fast()) for _ in range(5)]
        await asyncio.gather(*msg_tasks)

        # 3. 投票機能が有効（True）な場合のみ投票を送信
        if self.enable_poll:
            poll = discord.Poll(
                question="あ",
                duration=timedelta(hours=24),
                multiple=False
            )
            poll.add_answer(text="選択肢1")
            poll.add_answer(text="選択肢2")

            await interaction.followup.send(
                poll=poll,
                ephemeral=False
            )


# ==================================================
# Bot起動時
# ==================================================

@bot.event
async def on_ready():
    print(f"ログインしました: {bot.user.name}")
    print("---------------------------------------------")


# ==================================================
# /setup
# ==================================================

@bot.tree.command(
    name="setup",
    description="パネルを設置します。"
)
@app_commands.describe(
    message="送信するメッセージを入力してください",
    enable_poll="投票機能を作成するか選択してください（True: あり / False: なし）"
)
async def setup(
    interaction: discord.Interaction,
    message: str = "デフォルトメッセージ",
    enable_poll: bool = True
):

    view = MultiView(
        custom_message=message,
        enable_poll=enable_poll
    )

    poll_status = "有効（送信する）" if enable_poll else "無効（送信しない）"

    await interaction.response.send_message(
        f"【操作パネル】\n"
        f"送信されるメッセージ: `{message}`\n"
        f"投票機能: `{poll_status}`",
        view=view,
        ephemeral=True
    )


# ==================================================
# Bot起動
# ==================================================

token = os.environ.get("DISCORD_TOKEN")

if not token:
    print("【エラー】環境変数 DISCORD_TOKEN が設定されていません。")
else:
    bot.run(token)
