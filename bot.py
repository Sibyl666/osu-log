import discord
from os import listdir, path, environ
from discord.ext import commands

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="%", intents=intents)


if __name__ == "__main__":
    for extension in [file.replace(".py", "") for file in listdir("cogs/") if path.isfile(f"cogs/{file}")]:
        bot.load_extension(f"cogs.{extension}")


@bot.event
async def on_ready():
    print("Bot Ready")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return

    await ctx.send(error)


bot.run(environ.get("token"))
