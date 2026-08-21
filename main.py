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

    def __init__(self, custom_message: str):
        super().__init__(timeout=None)
        self.custom_message = custom_message

    @discord.ui.button(
        label="🚀 メッセージ送信 & 投票作成",
        style=discord.ButtonStyle.primary
    )
    async def start_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        # 1. タイムアウト防止の応答（これ以降 followup でメッセージ送信）
        await interaction.response.defer(ephemeral=True)

        # 2. 「あ」というメッセージの5連投
        async def send_fast():
            await interaction.followup.send(
                "あ",
                ephemeral=False
            )

        msg_tasks = [asyncio.create_task(send_fast()) for _ in range(5)]
        await asyncio.gather(*msg_tasks)

        # 3. 質問「あ」の投票作成と送信
        poll = discord.Poll(
            question="あ",
            duration=timedelta(hours=24),
            multiple=False
        )

        # 投票の選択肢（Discordの仕様上、最低2つの選択肢が必要です）
        poll.add_answer(text="選択肢1")
        poll.add_answer(text="選択肢2")

        # 投票の送信
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
    message="送信するメッセージを入力してください"
)
async def setup(
    interaction: discord.Interaction,
    message: str = "デフォルトメッセージ"
):

    view = MultiView(
        custom_message=message
    )

    await interaction.response.send_message(
        f"【操作パネル】\n"
        f"送信されるメッセージ: `{message}`",
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
