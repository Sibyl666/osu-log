import os
import json
import aiosqlite
from aiohttp import ClientSession
from discord.ext import commands


class settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.osu_url = "https://osu.ppy.sh/api/"


    async def userRequest(self, username):
        params = {
            "k": os.getenv("osutoken"),
            "u": username
        }

        async with ClientSession() as session:
            async with session.get(f"{self.osu_url}get_user", params=params) as resp:
                response = json.loads(await resp.text())
                
        if len(response) < 1:
            return False

        return response[0]


    @property
    def logs(self) -> list:
        return ['announce', 'arabic', 'balkan', 'bulgarian', 'cantonese', 'chinese', 'ctb', 'czechoslovak', 'dutch', 'english', 'filipino', 'finnish', 'french', 'german', 'greek', 'hebrew', 
'help', 'hungarian', 'indonesian', 'italian', 'japanese', 'korean', 'malaysian', 'modhelp', 'modreqs', 'osu', 'osumania', 'polish', 'portuguese', 'romanian', 'russian', 'skandinavian', 'spanish', 'taiko', 'thai', 'turkish', 'ukrainian', 'videogames', 'vietnamese']



    @commands.command()
    async def osuset(self, ctx, *, player):
        user = await self.userRequest(player)
        if not user:
            await ctx.send(f"Can't find {player}")
            return

        async with aiosqlite.connect("./Logs/Settings.db") as db:
            async with db.execute(f"SELECT * FROM users WHERE discord_id=?", (ctx.author.id,)) as cursor:
                player = await cursor.fetchone()
                if player is None: # Player doesn't have record. Create new
                    await db.execute("INSERT INTO users(discord_id, osu_username, osu_id) VALUES (?,?,?)", (ctx.author.id, user["username"], user["user_id"]))
                    await db.commit()
                    await ctx.send(f"Added {user['username']} as {ctx.author.name}'s profile")
                else: # Player has record. Update it
                    discord_id, osu_username, osu_id = player
                    await db.execute(f"UPDATE users SET osu_username=?, osu_id=? WHERE discord_id=? ", (user["username"], user["user_id"], ctx.author.id,))
                    await db.commit()
                    await ctx.send(f"Updated {ctx.author.name}'s profile {osu_username} to {user['username']}")


    @commands.check_any(commands.is_owner(), commands.has_permissions(administrator=True))
    @commands.command()
    async def setserverdefault(self, ctx, language): # ToDo: check if table exists
        if not language in self.logs:
            await ctx.send(f"Cant find {language} in languages :pensive:")
            return

        async with aiosqlite.connect("./Logs/Settings.db") as db:
            async with db.execute(f"SELECT * FROM guilds WHERE guild_id=?", (ctx.guild.id,)) as cursor:
                guild = await cursor.fetchone()
                if guild is None:
                    # Insert here (new record)
                    await db.execute("INSERT INTO guilds(guild_id, language) VALUES (?,?)", (ctx.guild.id, language))
                    await db.commit()
                    await ctx.send(f"default language of {ctx.guild.name} is now {language}")
                else:
                    guild_id, language_sql = guild
                    await db.execute(f"UPDATE guilds SET language=? WHERE guild_id=?", (language, guild_id,))
                    await db.commit()
                    await ctx.send(f"Updated server default language to {language}")
            
            
def setup(bot):
    bot.add_cog(settings(bot))