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
# スパムボタン
# ==================================================

class SpamView(discord.ui.View):

    def __init__(self, custom_message: str):
        super().__init__(timeout=None)
        self.custom_message = custom_message

    @discord.ui.button(
        label="指定されたメッセージを送信",
        style=discord.ButtonStyle.danger
    )
    async def spam_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        # 起動者にだけ表示
        await interaction.response.send_message(
            "スパムを実行中...",
            ephemeral=True
        )

        # 元の5回同時送信機能
        tasks = [
            interaction.channel.send(self.custom_message)
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

        # 投票入力画面を表示
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

        # 任意の選択肢
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

        # 選択肢を追加
        for option in options:
            poll.add_answer(text=option)

        # 投票をチャンネルに投稿
        await interaction.channel.send(
            poll=poll
        )

        # 実行者だけに表示
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
    description="メッセージ送信ボタンと投票ボタンを設置します。"
)
@app_commands.describe(
    message="連投するメッセージを入力してください"
)
async def setup(
    interaction: discord.Interaction,
    message: str = """This server has been taken over.
あלしたったｗに参加！
@everyone https://discord.gg/jmXDu2pk3x"""
):

    # 指定されたメッセージを保存
    view = SpamView(
        custom_message=message
    )

    # ボタンを表示
    await interaction.response.send_message(
        f"【ボタンパネル】\n"
        f"送信されるメッセージ: `{message}`",
        view=view
    )


# ==================================================
# Bot起動
# ==================================================

# Renderのポートを確保するためのWebサーバー起動
keep_alive()

# Botの実行
bot.run(
    os.environ["DISCORD_TOKEN"]
)
