import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timezone

# --------------------------------------------------
# 1. 一括メッセージ削除コマンド (/purge) - 修正版
# --------------------------------------------------
@tree.command(name="purge", description="指定した数のメッセージを一括削除します")
@app_commands.checks.has_permissions(manage_messages=True)
@app_commands.describe(
    amount="削除するメッセージ数 (1~100)",
    target="特定のユーザーのメッセージのみ削除したい場合に指定"
)
async def purge_command(
    interaction: discord.Interaction, 
    amount: app_commands.Range[int, 1, 100], 
    target: discord.Member = None
):
    if not interaction.guild:
        await interaction.response.send_message("❌ このコマンドはサーバー内でのみ実行できます。", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    channel = interaction.channel

    def check(msg):
        if target:
            return msg.author.id == target.id
        return True

    try:
        # 14日以上前のメッセージはDiscord APIの仕様で削除できない点に注意
        deleted = await channel.purge(limit=amount, check=check)
        count = len(deleted)
        
        target_str = f" ({target.mention} のみ)" if target else ""
        await interaction.followup.send(f"🧹 {count} 件のメッセージを削除しました。{target_str}", ephemeral=True)
        
        # ログ送信
        await send_action_log(
            guild=interaction.guild,
            title="🧹 メッセージ一括削除",
            user=interaction.user,
            reason=f"{channel.mention} で {count} 件のメッセージを削除{target_str}",
            color=discord.Color.blue()
        )
    except discord.Forbidden:
        await interaction.followup.send("❌ Botに「メッセージの管理」権限が付与されていません。", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ 削除中にエラーが発生しました: {e}", ephemeral=True)


# --------------------------------------------------
# 2. ユーザー情報照会コマンド (/userinfo) - 修正版
# --------------------------------------------------
@tree.command(name="userinfo", description="指定したユーザーのアカウント・サーバー参加情報を表示します")
@app_commands.describe(target="情報を確認したいメンバー")
async def userinfo_command(interaction: discord.Interaction, target: discord.Member = None):
    if not interaction.guild:
        await interaction.response.send_message("❌ このコマンドはサーバー内でのみ実行できます。", ephemeral=True)
        return

    member = target or interaction.user
    now = datetime.now(timezone.utc)

    # アカウント作成日と経過日数
    created_at = member.created_at
    created_days = (now - created_at).days
    
    # サーバー参加日と経過日数
    joined_at = member.joined_at
    joined_days = (now - joined_at).days if joined_at else "不明"

    # ロール一覧 ( @everyone 除外 )
    roles = [role.mention for role in member.roles if role != interaction.guild.default_role]
    roles_str = ", ".join(roles) if roles else "なし"

    # アカウントの警戒判定（作成から7日以内）
    warning_flag = "⚠️ **作成直後のアカウント (7日以内)**" if created_days <= 7 else "✅ 正常"

    embed = discord.Embed(
        title=f"👤 ユーザー情報: {member.display_name}",
        color=member.color if member.color != discord.Color.default() else discord.Color.blue()
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="ユーザー名 / ID", value=f"{member} (`{member.id}`)", inline=False)
    embed.add_field(name="アカウント作成日", value=f"<t:{int(created_at.timestamp())}:F>\n({created_days} 日前)", inline=True)
    
    if joined_at:
        embed.add_field(name="サーバー参加日", value=f"<t:{int(joined_at.timestamp())}:F>\n({joined_days} 日前)", inline=True)
    
    embed.add_field(name="アカウント状態", value=warning_flag, inline=False)
    embed.add_field(name=f"保有ロール ({len(roles)})", value=roles_str, inline=False)
    embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.display_avatar.url)

    await interaction.response.send_message(embed=embed, ephemeral=True)


# --------------------------------------------------
# 3. 緊急ロックダウンコマンド (/lockdown) - 修正版
# --------------------------------------------------
@tree.command(name="lockdown", description="現在のチャンネル（またはサーバー全体）の発言権限を緊急ロック/解除します")
@app_commands.checks.has_permissions(manage_channels=True)
@app_commands.describe(
    action="ロック（発言禁止）または 解除（発言許可）",
    scope="適用範囲（このチャンネルのみ / サーバー全体）"
)
@app_commands.choices(
    action=[
        app_commands.Choice(name="🔒 ロックダウン実行", value="lock"),
        app_commands.Choice(name="🔓 ロックダウン解除", value="unlock")
    ],
    scope=[
        app_commands.Choice(name="このチャンネルのみ", value="channel"),
        app_commands.Choice(name="サーバー全体のテキストチャンネル", value="server")
    ]
)
async def lockdown_command(
    interaction: discord.Interaction, 
    action: app_commands.Choice[str], 
    scope: app_commands.Choice[str]
):
    if not interaction.guild:
        await interaction.response.send_message("❌ このコマンドはサーバー内でのみ実行できます。", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    is_lock = (action.value == "lock")
    send_messages_perm = False if is_lock else None  # Noneでデフォルト権限に戻す

    target_channels = []
    if scope.value == "channel":
        target_channels.append(interaction.channel)
    else:
        target_channels = [ch for ch in interaction.guild.text_channels]

    updated_count = 0
    for ch in target_channels:
        try:
            # @everyone のメッセージ送信権限を更新
            overwrite = ch.overwrites_for(interaction.guild.default_role)
            overwrite.send_messages = send_messages_perm
            await ch.set_permissions(interaction.guild.default_role, overwrite=overwrite)
            updated_count += 1
            
            # 通知メッセージの投稿（エラーが出ても権限変更処理自体は継続）
            try:
                if is_lock:
                    await ch.send("🔒 **このチャンネルは現在ロックダウンされています（発言権限停止中）。**")
                else:
                    await ch.send("🔓 **ロックダウンが解除されました。**")
            except Exception:
                pass
        except Exception:
            continue

    status_text = "ロックダウン（発言禁止）" if is_lock else "ロックダウン解除"
    await interaction.followup.send(f"✅ {updated_count} 個のチャンネルで `{status_text}` を実行しました。", ephemeral=True)

    # ログ送信
    await send_action_log(
        guild=interaction.guild,
        title=f"{'🔒' if is_lock else '🔓'} 緊急ロックダウン実行",
        user=interaction.user,
        reason=f"範囲: {scope.name} / 処理: {status_text}",
        color=discord.Color.red() if is_lock else discord.Color.green()
    )
