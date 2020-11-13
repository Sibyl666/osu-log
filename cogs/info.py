from discord.ext import commands


class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.command()
    async def invite(self, ctx):
        await ctx.send("https://discord.com/api/oauth2/authorize?client_id=700736599146758145&permissions=8192&scope=bot")


def setup(bot):
    bot.add_cog(Info(bot))
