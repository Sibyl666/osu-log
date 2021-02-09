import aiosqlite
import sqlite3
import random
import asyncio
import discord
import re
from io import StringIO
from collections import Counter
from discord.ext import commands


def fix_username(player: str) -> str:
    return player.replace(" ", "_")


def SplitWordTwo(WordList: list) -> tuple:
    Middle = len(WordList) / 2
    FirstHalf = "".join(WordList[:int(Middle)])
    SecondHald = "".join(WordList[int(Middle):])
    return (FirstHalf, SecondHald)
    

def MaxLength(messages: list) -> int:
    usernameLengthList = [len(message[2]) for message in messages]
    return max(usernameLengthList)


def regexp(expr: str, message: str) -> str:
    try:
        match = re.search(r'\b{}\b'.format(expr), message, re.IGNORECASE)
        if not match is None:
            return True
    except:
        return False


class Chat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.CheckIndexes()

    @property
    def logs(self) -> list:
        return ['announce', 'arabic', 'balkan', 'bulgarian', 'cantonese', 'chinese', 'ctb', 'czechoslovak', 'dutch', 'english', 'filipino', 'finnish', 'french', 'german', 'greek', 'hebrew', 
'help', 'hungarian', 'indonesian', 'italian', 'japanese', 'korean', 'malaysian', 'modhelp', 'modreqs', 'osu', 'osumania', 'polish', 'portuguese', 'romanian', 'russian', 'skandinavian', 'spanish', 'taiko', 'thai', 'turkish', 'ukrainian', 'videogames', 'vietnamese']

    def CheckIndexes(self):
        conn = sqlite3.connect("./Logs/Chatlogs.db")
        conn.execute(f"CREATE INDEX IF NOT EXISTS TurkishIndexTable on turkish(username)")
        conn.close()

    async def add_reaction(self, ctx, msg, content_length):
        await msg.add_reaction("♿")

        def check_reaction(react, user):
            if react.message.id != msg.id:
                return False
            if user != ctx.message.author:
                return False
            if str(react.emoji) != "♿":
                return False
            return True

        try:
            await self.bot.wait_for("reaction_add", timeout=20, check=check_reaction)
            await msg.clear_reactions()
        except asyncio.TimeoutError:
            return await msg.clear_reactions()

        msg_splitted = msg.content.splitlines()[:3]
        language = msg_splitted[0].split(" ")[1].strip()
        date = msg_splitted[1].split(" ")[1].strip()
        index = int(msg_splitted[2].split(" ")[1].strip())

        if index < 5:
            index = 5

        async with aiosqlite.connect("./Logs/Chatlogs.db") as conn:
            async with conn.execute(f"SELECT * FROM {language} LIMIT {index - 6}, 11") as cursor:
                messages = await cursor.fetchall()

        MaxLengthint = MaxLength(messages)

        chatmsg = "```"
        for message in messages:
            indexx, hour, username, message, date = message # assign stuff of message
            addSpaceLenght = MaxLengthint - len(username)
            chatmsg += f"{hour} {username}:{' '*addSpaceLenght} {message} \n"

        chatmsg += "```"

        context_msg = await ctx.send(chatmsg)
        await self.add_reaction_scroll(ctx, index, language, context_msg, content_length, date)
        return await msg.clear_reactions()


    async def add_reaction_scroll(self, ctx, index, language, context_msg, content_length, date):
        startOfMessages = index - 5
        if content_length < 5:
            return

        reacts_emojis = ["⏫", "⏬"]
        for react in reacts_emojis:
            await context_msg.add_reaction(react)

        def check_reactions_arrow(reaction, user):
            if reaction.message.id != context_msg.id:
                return False
            if user != ctx.author:
                return False
            if str(reaction.emoji) not in reacts_emojis:
                return False
            return True

        while True:
            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=25, check=check_reactions_arrow)
                await reaction.remove(user)
            except asyncio.TimeoutError:
                return await context_msg.clear_reactions()

            react_list = [reaction.emoji for reaction in reaction.message.reactions]
            if str(reaction.emoji) == "⏫":
                startOfMessages -= 3

                if "⏬" not in react_list:
                    await context_msg.clear_reactions()
                    for react in reacts_emojis:
                        await context_msg.add_reaction(react)
                
                if startOfMessages <= 0:
                    startOfMessages = 0
                    await reaction.clear()

                    
            elif str(reaction.emoji) == "⏬":
                startOfMessages += 3
                
                if "⏫" not in react_list:
                    await context_msg.clear_reactions()
                    for react in reacts_emojis:
                        await context_msg.add_reaction(react)
                
                if startOfMessages >= content_length:
                    startOfMessages = content_length - 3
                    await reaction.clear()


            async with aiosqlite.connect("./Logs/Chatlogs.db") as conn:
                async with conn.execute(f"SELECT * FROM {language} LIMIT {startOfMessages}, 10") as cursor:
                    messages = await cursor.fetchall()

            MaxLengthint = MaxLength(messages)

            chatmsg = "```"
            for message in messages:
                index, hour, username, message, date = message
                addSpaceLenght = MaxLengthint - len(username)
                chatmsg += f"{hour} {username}:{' '*addSpaceLenght} {message} \n"
            chatmsg += "```"

            await context_msg.edit(content=chatmsg)


    @staticmethod
    async def find_whole_word(word: str, message: str) -> bool:
        msg = re.search(r"\b{}\b".format(word), message, re.IGNORECASE)
        if msg:
            return msg
        return False


    @commands.command()
    async def random(self, ctx, player:fix_username = None, language: str = None):
        """
            Gets Random Message
        """
        if player is None and language is None: # Nothing given select random player and language
            language = random.choice(self.logs)
            async with aiosqlite.connect("./Logs/Chatlogs.db") as conn:
                async with conn.execute(f"SELECT * FROM {language} WHERE id IN (SELECT id FROM {language} ORDER BY RANDOM() LIMIT 1)") as cursor:
                    message = (await cursor.fetchall())[0]
        elif player not in self.logs: # player given
            if language is None: # player given, language didn't. Select default language
                async with aiosqlite.connect("./Logs/Settings.db") as db:
                    async with db.execute(f"SELECT language FROM guilds WHERE guild_id=?", (ctx.guild.id,)) as cursor:
                        language = await cursor.fetchone()
                        if language is None: # can't find default language.
                            embed = discord.Embed(description="You have to specify language if server doesn't have default one")
                            embed.set_author(name="Help Menu")
                            embed.add_field(name="Example", value="```%random sibyl turkish```")
                            embed.add_field(name="Set server default", value="```%setserverdefault turkish```")
                            await ctx.send("Language is a required argument that is missing.", embed=embed)
                            return
                        language = language[0]

            async with aiosqlite.connect("./Logs/Chatlogs.db") as conn:
                async with await conn.execute(f"SELECT * FROM {language} WHERE username=? ", (player,)) as cursor:
                    messages = await cursor.fetchall()
                    
                    if len(messages) < 1:
                        await ctx.send(f"Can't find messages of {player.replace('%', '')} in {language}")
                        return

                    message = random.choice(messages) # Random message
        else: # language given
            language = player
            if language not in self.logs:
                await ctx.send(f"Can't find {language} in languages")
                return

            async with aiosqlite.connect("./Logs/Chatlogs.db") as conn:
                async with conn.execute(f"SELECT * FROM {language} WHERE id IN (SELECT id FROM {language} ORDER BY RANDOM() LIMIT 1)") as cursor:
                    message = (await cursor.fetchall())[0]

        index, hour, username, message, date = message # assign stuff of message

        if index < 5:
            index = 5

        msg = f"{hour} {username}: {message}"
        random_msg = f"```{index} | {msg} \n```"

        try:
            msg = await ctx.send(f"""
            **Language**: {language}\n**Date**: {date}\n**Index**: {index}\n{random_msg}
            """)
            async with aiosqlite.connect("./Logs/Chatlogs.db") as conn:
                async with conn.execute(f"SELECT max(Id) FROM {language}") as cursor:
                    index = (await cursor.fetchone())[0]

            await self.add_reaction(ctx, msg, index)
        except:
            pass


    @commands.cooldown(1, 3)
    @commands.command()
    async def chat(self, ctx, language:str = None, chatlimit: int = 10):
        """
            Last 10 messages of given language chat
        """

        try:
            chatlimit = int(language)
            async with aiosqlite.connect("./Logs/Settings.db") as db:
                async with db.execute(f"SELECT language FROM guilds WHERE guild_id=?", (ctx.guild.id,)) as cursor:
                    language = await cursor.fetchone()
                    language = language[0]
        except:
            pass
        
        if language is None:
            async with aiosqlite.connect("./Logs/Settings.db") as db:
                async with db.execute(f"SELECT language FROM guilds WHERE guild_id=?", (ctx.guild.id,)) as cursor:
                    language = await cursor.fetchone()
                    if language is None:
                        embed = discord.Embed(description="You don't need language if server has default language\nLooks like this server doesn't have default")
                        embed.set_author(name="Help Menu")
                        embed.add_field(name="Example", value="```%chat turkish 30```")
                        await ctx.send("Language is a required argument that is missing.", embed=embed)
                        return
                    language = language[0]
        elif language not in self.logs:
            await ctx.send(f"Can't find {language} in languages :pensive:")
            return

        async with aiosqlite.connect("./Logs/Chatlogs.db") as conn:
            async with conn.execute(f"SELECT * FROM {language} ORDER BY id DESC limit {chatlimit}") as cursor:
                messages = await cursor.fetchall()
            
        MaxLengthint = MaxLength(messages)

        chatmsg = "```"
        for message in reversed(messages):
            index, hour, username, message, date = message # assign stuff of message
            addSpaceLenght = MaxLengthint - len(username)
            chatmsg += f"{hour} {username}:{' '*addSpaceLenght} {message}\n"
        chatmsg += "```"

        try:
            await ctx.send(chatmsg)
        except Exception as err:
            await ctx.send(err)
            
    @commands.cooldown(1, 3)
    @commands.command(aliases=["get"])
    async def getuser(self, ctx, player: fix_username = None, language: str = None, limit=10):
        """
            Get player last messages
        """

        try:
            limit = int(language)
            async with aiosqlite.connect("./Logs/Settings.db") as db:
                async with db.execute(f"SELECT language FROM guilds WHERE guild_id=?", (ctx.guild.id,)) as cursor:
                    language = await cursor.fetchone()
                    language = language[0]
        except:
            pass

        if player is None: # check database if user has default
            async with aiosqlite.connect("./Logs/Settings.db") as db:
                async with db.execute(f"SELECT * FROM users WHERE discord_id=?", (ctx.author.id,)) as cursor:
                    player = await cursor.fetchone()
                    if player is None:
                        embed = discord.Embed(description="You have to specify player if you didn't set one")
                        embed.set_author(name="Help Menu")
                        embed.add_field(name="Example", value="```%getuser Sibyl turkish 30```")
                        embed.add_field(name="Set user", value="```%osuset Sibyl```")
                        await ctx.send("Player is a required argument that is missing.", embed=embed)
                        return
                    discord_id, player, osu_id = player

        if language is None: # check language if server has default
            async with aiosqlite.connect("./Logs/Settings.db") as db:
                async with db.execute(f"SELECT language FROM guilds WHERE guild_id=?", (ctx.guild.id,)) as cursor:
                    language = await cursor.fetchone()
                    if language is None:
                        embed = discord.Embed(description="You have to specify language if server doesn't have default one")
                        embed.set_author(name="Help Menu")
                        embed.add_field(name="Example", value="```%getuser Sibyl turkish 30```")
                        embed.add_field(name="Set server default", value="```%setserverdefault turkish```")
                        await ctx.send("Language is a required argument that is missing.", embed=embed)
                        return
                    language = language[0]
        elif language not in self.logs:
            await ctx.send(f"Can't find {language} in languages")
            return


        async with aiosqlite.connect("./Logs/Chatlogs.db") as db:
            async with db.execute(f"SELECT id, date, message FROM {language} WHERE username=? ", (player,)) as cursor:
                if limit < 0:
                    result = (await cursor.fetchall())[:abs(limit)]
                else:
                    result = (await cursor.fetchall())[-limit:]

        if len(result) < 1:
            await ctx.send(f"Can't find messages of {player} in {language}")
            return
        
        chatmsg = "```"
        for messageId, date, message in result:
            chatmsg += f"{messageId} | {date} {player}: {''.join(message)} \n"
        chatmsg += "```"

        try:
            await ctx.send(content=chatmsg)
        except Exception as err:
            await ctx.send(content=err)

    @commands.cooldown(1, 3)
    @commands.command()
    async def getcontext(self, ctx, messageId: int, limit: int = 10, language: str = None):
        if language is None: # check language if server has default
            async with aiosqlite.connect("./Logs/Settings.db") as db:
                async with db.execute(f"SELECT language FROM guilds WHERE guild_id=?", (ctx.guild.id,)) as cursor:
                    language = await cursor.fetchone()
                    if language is None:
                        embed = discord.Embed(description="You have to specify language if server doesn't have default one")
                        embed.set_author(name="Help Menu")
                        embed.add_field(name="Example", value="```%getcontext 11111```")
                        embed.add_field(name="Set server default", value="```%setserverdefault turkish```")
                        await ctx.send("Language is a required argument that is missing.", embed=embed)
                        return
                    language = language[0]
        elif language not in self.logs:
            await ctx.send(f"Can't find {language} in languages")
            return

        async with aiosqlite.connect("./Logs/Chatlogs.db") as db:
            async with db.execute(f"SELECT * FROM {language} WHERE id=?", (messageId,)) as cursor:
                context = await cursor.fetchone()
                if not context:
                    await ctx.send(f"Can't find messages with {messageId} id")
                    return
                index, hour, username, message, date = context

        message = f"```{hour} {username}: {message}```"
        msg = await ctx.send(f"""
            **Language**: {language}\n**Date**: {date}\n**Index**: {index}\n{message}
            """)

        async with aiosqlite.connect("./Logs/Chatlogs.db") as conn:
            async with conn.execute(f"SELECT max(Id) FROM {language}") as cursor:
                index = (await cursor.fetchone())[0]

        await self.add_reaction(ctx, msg, index)


    @commands.cooldown(1, 3)
    @commands.command()
    async def search(self, ctx, word: str = None, language: str = None, limit: int=10):
        """
            Search word in logs
        """
        
        try:
            limit = int(language)
            async with aiosqlite.connect("./Logs/Settings.db") as db:
                async with db.execute(f"SELECT language FROM guilds WHERE guild_id=?", (ctx.guild.id,)) as cursor:
                    language = await cursor.fetchone()
                    language = language[0]
        except:
            pass

        if word is None:
            embed = discord.Embed(description="You have to specify language if server doesn't have default one")
            embed.set_author(name="Help Menu")
            embed.add_field(name="Example", value="```%search \"Search stuff\" turkish 10```")
            embed.add_field(name="Set server default", value="```%setserverdefault turkish```")
            await ctx.send("Word is a required argument that is missing.", embed=embed)
            return

        if language is None: # check language if server has default
            async with aiosqlite.connect("./Logs/Settings.db") as db:
                async with db.execute(f"SELECT language FROM guilds WHERE guild_id=?", (ctx.guild.id,)) as cursor:
                    language = await cursor.fetchone()
                    if language is None:
                        embed = discord.Embed(description="You have to specify language if server doesn't have default one")
                        embed.set_author(name="Help Menu")
                        embed.add_field(name="Example", value="```%search \"Search stuff\" turkish 10```")
                        embed.add_field(name="Set server default", value="```%setserverdefault turkish```")
                        await ctx.send("Language is a required argument that is missing.", embed=embed)
                        return
                    language = language[0]
        elif language not in self.logs:
            await ctx.send(f"Can't find {language} in languages :pensive:")
            return

        async with aiosqlite.connect("./Logs/Chatlogs.db") as conn:
            await conn.create_function("REGEXP", 2, regexp)
            async with conn.execute(f"""SELECT * FROM {language} WHERE message REGEXP ? ORDER BY id DESC LIMIT {limit}""", (word,)) as cursor:
                messages = await cursor.fetchall()

        if len(messages) < 1:
            await ctx.send(f"Can't find message contains {word.replace('%', '')}")
            return

        MaxLengthint = MaxLength(messages)

        chatmsg = "```"
        for message in reversed(messages):
            index, hour, username, message, date = message # assign stuff of message
            addSpaceLenght = MaxLengthint - len(username)
            chatmsg += f"{index} | {hour} {username}:{' '*addSpaceLenght} {message} \n"
        chatmsg += "```"

        try:
            await ctx.send(content=chatmsg)
        except Exception as err:
            await ctx.send(content=err)


    @commands.cooldown(1, 3)
    @commands.command()
    async def stats(self, ctx, player: fix_username = None, language: str = None):
        """
            Stats of player based on chat logs
        """

        if player is None: # check database if user has default
            async with aiosqlite.connect("./Logs/Settings.db") as db:
                async with db.execute(f"SELECT * FROM users WHERE discord_id=?", (ctx.author.id,)) as cursor:
                    player = await cursor.fetchone()
                    if player is None:
                        embed = discord.Embed(description="You have to specify player if you didn't set one")
                        embed.set_author(name="Help Menu")
                        embed.add_field(name="Example", value="```%stats Sibyl turkish```")
                        await ctx.send("Player is a required argument that is missing.", embed=embed)
                        return
                    discord_id, player, osu_id = player

        if language is None: # check language if server has default
            async with aiosqlite.connect("./Logs/Settings.db") as db:
                async with db.execute(f"SELECT language FROM guilds WHERE guild_id=?", (ctx.guild.id,)) as cursor:
                    language = await cursor.fetchone()
                    if language is None:
                        embed = discord.Embed(description="You have to specify language if server doesn't have default one")
                        embed.set_author(name="Help Menu")
                        embed.add_field(name="Example", value="```%stats Sibyl turkish```")
                        await ctx.send("Language is a required argument that is missing.", embed=embed)
                        return
                    language = language[0]
        elif language not in self.logs:
            await ctx.send(f"Can't find {language} in languages")

        async with aiosqlite.connect("./Logs/Chatlogs.db") as conn:
            async with conn.execute(f"SELECT * FROM {language} WHERE username=? ", (player,)) as cursor:
                messages = (await cursor.fetchall())

        if len(messages) < 1:
            await ctx.send("Cant find player messages")
            return

        user_color = ctx.author.color
        embed = discord.Embed(color=user_color)
        embed.add_field(name="Message Count", value=len(messages), inline=True)

        words = []
        for message in messages:
            for word in message[3].split():
                if len(word) < 3:
                    continue
                
                words.append(word)

        counter = Counter(words)
        most_occur = counter.most_common(3)

        most_used_words_string = ""
        for count, word in enumerate(most_occur):
            word, counter = word
            most_used_words_string += f"{count} - {word} ({counter})\n"

        embed.add_field(name="Most Used Words", value=most_used_words_string, inline=True)

        index, hour, username, message, date = random.choice(messages)
        embed.add_field(name="Random Message", value=message, inline=False)

        await ctx.send(embed=embed)


    @commands.cooldown(1, 10)
    @commands.command()
    async def log(self, ctx, date: str, language: str = None):
        if language is None: # check language if server has default
            async with aiosqlite.connect("./Logs/Settings.db") as db:
                async with db.execute(f"SELECT language FROM guilds WHERE guild_id=?", (ctx.guild.id,)) as cursor:
                    language = await cursor.fetchone()
                    if language is None:
                        raise Exception("language is a required argument that is missing.")
                    language = language[0]

        async with aiosqlite.connect("./Logs/Chatlogs.db") as conn:
            async with conn.execute(f"SELECT * FROM {language} WHERE date='{date}'") as cursor:
                messages = (await cursor.fetchall())
        
        if len(messages) < 1:
            await ctx.send("Can't find messages :pensive:")
            return

        file_string = ""
        for message in messages:
            msgid, hour, username, message, date = message
            file_string += f"{hour} {username} :{message}\n"
            
        with StringIO(file_string) as stream_str:
            await ctx.send(file=discord.File(stream_str, filename=f"{date}.log"))



def setup(bot):
    bot.add_cog(Chat(bot))
