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

        # 実行者にだけ通知を表示
        await interaction.response.send_message(
            "処理を実行中...",
            ephemeral=True
        )

        # 5回同時送信
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
            duration=24,
            multiple=False
        )

        for option in options:
            poll.add_answer(text=option)

        await interaction.channel.send(
            poll=poll
        )

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
    message="送信するメッセージを入力してください"
)
async def setup(
    interaction: discord.Interaction,
    message: str = "デフォルトメッセージ"
):

    view = MultiView(
        custom_message=message
    )

    # ephemeral=True でコマンド実行者だけにパネルを表示
    await interaction.response.send_message(
        f"【操作パネル】\n"
        f"送信されるメッセージ: `{message}`",
        view=view,
        ephemeral=True
    )


# ==================================================
# Bot起動
# ==================================================

keep_alive()

# DISCORD_TOKEN のみを読み込み
token = os.environ.get("DISCORD_TOKEN")

if not token:
    raise ValueError("環境変数に DISCORD_TOKEN が設定されていません。")

bot.run(token)
