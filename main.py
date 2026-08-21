import discord
from discord.ext import commands
from discord import app_commands
import os
import asyncio
from keep_alive import keep_alive

intents = discord.Intents.default()
intents.message_content = True


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
# 投票機能パネル
# ==================================================

class PollView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="📊 投票を作成",
        style=discord.ButtonStyle.primary
    )
    async def poll_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        # 投票入力画面を表示（押した本人のみに表示されます）
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

        # 選択肢を作成
        options = [
            self.option1.value,
            self.option2.value
        ]

        if self.option3.value:
            options.append(self.option3.value)

        if self.option4.value:
            options.append(self.option4.value)

        # Discord公式Pollを作成
        poll = discord.Poll(
            question=self.question.value,
            duration=24,
            multiple=False
        )

        for option in options:
            poll.add_answer(text=option)

        # 完成した投票をチャンネル全体に投稿
        await interaction.channel.send(
            poll=poll
        )

        # 実行者だけに完了メッセージを表示
        await interaction.response.send_message(
            "✅ 投票を作成しました！",
            ephemeral=True
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
    description="投票設置用パネルを表示します。"
)
async def setup(
    interaction: discord.Interaction
):

    view = PollView()

    # ephemeral=True により、コマンド実行者だけにパネルが表示されます
    await interaction.response.send_message(
        "【投票作成パネル】\n下のボタンを押して投票を作成してください。",
        view=view,
        ephemeral=True
    )


# ==================================================
# Bot起動
# ==================================================

keep_alive()

# DISCORD_TOKEN（大文字）のみを読み込み
token = os.environ.get("DISCORD_TOKEN")

if not token:
    raise ValueError("環境変数に DISCORD_TOKEN が設定されていません。")

bot.run(token)
