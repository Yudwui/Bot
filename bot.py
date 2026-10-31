import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional

# Вставьте сюда скопированный токен бота из Developer Portal
TOKEN = "MTU2MTU4Nzg4MDYzNDA5NzcyNA.GZ8uSD.iepM7N_i0juvKp6KNqae3AmvoHDM31MaE1CI2k"

intents = discord.Intents.default()
intents.members = True


class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Регистрация слеш-команд в Discord
        await self.tree.sync()
        print("Слеш-команды синхронизированы!")

    async def on_ready(self):
        print(f"Бот успешно запущен как: {self.user} (ID: {self.user.id})")


bot = MyBot()


# Команда 1: /hello
@bot.tree.command(name="hello", description="Поприветствовать пользователя")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"Привет, {interaction.user.mention}! 👋"
    )


# Команда 2: /ping
@bot.tree.command(name="ping", description="Проверка пинга бота")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f"🏓 Понг! Задержка: `{latency} мс`")


# Команда 3: /avatar
@bot.tree.command(name="avatar", description="Показать аватар пользователя")
@app_commands.describe(member="Участник сервера (оставьте пустым для своего аватара)")
async def avatar(
    interaction: discord.Interaction,
    member: Optional[discord.Member] = None
):
    target = member or interaction.user

    embed = discord.Embed(
        title=f"Аватар: {target.display_name}",
        color=discord.Color.blue()
    )
    embed.set_image(url=target.display_avatar.url)

    await interaction.response.send_message(embed=embed)


if __name__ == "__main__":
    bot.run(TOKEN)