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
# パネル機能
# ==================================================

class MultiView(discord.ui.View):

    def __init__(self, custom_message: str):
        super().__init__(timeout=None)
        self.custom_message = custom_message

    @discord.ui.button(
        label="指定されたメッセージを送信",
        style=discord.ButtonStyle.danger
    )
    async def send_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        # 最初の応答（Interactionの処理を開始）
        await interaction.response.send_message(
            "処理を実行中...",
            ephemeral=True
        )

        # 外部アプリ（User Install）でも動作するよう followup を使用
        tasks = [
            interaction.followup.send(
                self.custom_message,
                ephemeral=False
            )
            for _ in range(5)
        ]

        await asyncio.gather(*tasks)

    @discord.ui.button(
        label="📊 投票を作成",
        style=discord.ButtonStyle.primary
    )
    async def poll_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.send_modal(
            PollModal()
        )


# ==================================================
# 投票入力画面
# ==================================================

class PollModal(
    discord.ui.Modal,
    title="📊 投票を作成"
):

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

        # 外部アプリ対応のため channel.send ではなく followup で送信
        await interaction.response.send_message(
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
    description="メッセージ送信ボタンと投票ボタンを設置します。"
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

    # コマンド実行者だけにパネルを表示
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
