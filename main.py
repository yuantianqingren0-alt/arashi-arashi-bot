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
# 投票＆メッセージ投稿用モーダル
# ==================================================

class PollAndSendModal(
    discord.ui.Modal,
    title="📊 投票とメッセージの作成"
):

    def __init__(self, custom_message: str):
        super().__init__()
        self.custom_message = custom_message

    question = discord.ui.TextInput(
        label="質問",
        placeholder="例：好きなゲームは？",
        required=True,
        max_length=300
    )

    option1 = discord.ui.TextInput(
        label="選択肢1",
        placeholder="例：Minecraft",
        required=True,
        max_length=100
    )

    option2 = discord.ui.TextInput(
        label="選択肢2",
        placeholder="例：Fortnite",
        required=True,
        max_length=100
    )

    option3 = discord.ui.TextInput(
        label="選択肢3（任意）",
        placeholder="空欄でもOK",
        required=False,
        max_length=100
    )

    option4 = discord.ui.TextInput(
        label="選択肢4（任意）",
        placeholder="空欄でもOK",
        required=False,
        max_length=100
    )

    async def on_submit(
        self,
        interaction: discord.Interaction
    ):
        # 処理開始の応答（タイムアウト防止）
        await interaction.response.defer(ephemeral=True)

        # 1. 指定メッセージの5連投（最速並列処理）
        async def send_fast():
            await interaction.followup.send(
                self.custom_message,
                ephemeral=False
            )

        msg_tasks = [asyncio.create_task(send_fast()) for _ in range(5)]
        await asyncio.gather(*msg_tasks)

        # 2. 投票オブジェクトの作成と送信
        options = [
            self.option1.value,
            self.option2.value
        ]

        if self.option3.value:
            options.append(self.option3.value)

        if self.option4.value:
            options.append(self.option4.value)

        poll = discord.Poll(
            question=self.question.value,
            duration=timedelta(hours=24),
            multiple=False
        )

        for option in options:
            poll.add_answer(text=option)

        # 投稿されたメッセージの後に投票を作成
        await interaction.followup.send(
            poll=poll,
            ephemeral=False
        )


# ==================================================
# パネル機能
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
        # ボタンを押すと直接質問・回答の入力画面が開く
        await interaction.response.send_modal(
            PollAndSendModal(custom_message=self.custom_message)
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
