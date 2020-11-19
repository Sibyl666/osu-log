import os
import re
import sqlite3
import aiosqlite
import random
import asyncio
import discord
import itertools
from collections import Counter
from aiofiles import open
from discord.ext import commands


def fix_username(player: str) -> str:
    return player.replace(" ", "_")


def add_percent(word: str) -> str:
    return f"%{word}%"


class Chat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @property
    async def logs(self) -> list:
        return ['announce', 'arabic', 'balkan', 'bulgarian', 'cantonese', 'chinese', 'ctb', 'czechoslovak', 'dutch', 'english', 'filipino', 'finnish', 'french', 'german', 'greek', 'hebrew', 
'help', 'hungarian', 'indonesian', 'italian', 'japanese', 'korean', 'malaysian', 'modhelp', 'modreqs', 'osu', 'osumania', 'polish', 'portuguese', 'romanian', 'russian', 'skandinavian', 'spanish', 'taiko', 'thai', 'turkish', 'ukrainian', 'videogames', 'vietnamese']


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

        chatmsg = "```"
        for message in messages:
            indexx, hour, username, message, date = message # assign stuff of message
            chatmsg += f"{hour} {username}:{message} \n"

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

            chatmsg = "```"
            for message in messages:
                index, hour, username, message, date = message
                chatmsg += f"{hour} {username}:{message} \n"
            chatmsg += "```"

            await context_msg.edit(content=chatmsg)


    @staticmethod
    async def find_whole_word(word: str, message: str) -> bool:
        msg = re.search(r"\b{}\b".format(word), message, re.IGNORECASE)
        if msg:
            return msg
        return False


    @commands.command()
    async def random(self, ctx, language: str = None):
        """
            Gets Random Message
        """
        
        if not language:
            random_language = random.choice(await self.logs)
        else:
            random_language = language

        async with aiosqlite.connect("./Logs/Chatlogs.db") as conn:
            async with conn.execute(f"SELECT * FROM {random_language} WHERE id IN (SELECT id FROM {random_language} ORDER BY RANDOM() LIMIT 1)") as cursor:
                message = await cursor.fetchall()

        index, hour, username, message, date = message[0] # assign stuff of message

        if index < 5:
            index = 5

        msg = f"{hour} {username}:{message}"
        random_msg = f"```{index} | {msg} \n```"

        try:
            msg = await ctx.send(f"""
            **Language**: {random_language}\n**Date**: {date}\n**Index**: {index}\n{random_msg}
            """)
            async with aiosqlite.connect("./Logs/Chatlogs.db") as conn:
                async with conn.execute(f"SELECT * FROM {random_language} ORDER BY id DESC LIMIT 1") as cursor:
                    index, hour, username, message, date = (await cursor.fetchall())[0]

            await self.add_reaction(ctx, msg, index)
        except:

            pass


    @commands.cooldown(1, 3)
    @commands.command()
    async def chat(self, ctx, language, chatlimit: int = 10):
        """
            Last 10 messages of given language chat
        """
        
        if language not in await self.logs:
            await ctx.send("Cant find language | Example: #turkish")
            return

        async with aiosqlite.connect("./Logs/Chatlogs.db") as conn:
            async with conn.execute(f"SELECT * FROM {language} ORDER BY id DESC limit {chatlimit}") as cursor:
                messages = await cursor.fetchall()
            
        
        chatmsg = "```"
        for message in reversed(messages):
            index, hour, username, message, date = message # assign stuff of message
            chatmsg += f"{hour} {username}:{message}\n"
        chatmsg += "```"

        try:
            await ctx.send(chatmsg)
        except Exception as err:
            await ctx.send(err)
            

    @commands.cooldown(1, 3)
    @commands.command()
    async def getrandom(self, ctx, player: add_percent, language: str):
        """ 
            Get random message from given player
        """

        async with aiosqlite.connect("./Logs/Chatlogs.db") as conn:
            async with await conn.execute(f"SELECT * FROM {language} WHERE username LIKE ?", (player,)) as cursor:
                messages = await cursor.fetchall()

        if len(messages) < 1:
            await ctx.send(f"Can't find messages of {player.replace('%', '')}")
            return

        random_message = random.choice(messages) # Random message
        index, hour, username, message, date = random_message # assign stuff of message
        chatmsg = f"{hour} {username}:{message}"

        async with aiosqlite.connect("./Logs/Chatlogs.db") as conn:
            async with conn.execute(f"SELECT * FROM {language} ORDER BY id DESC LIMIT 1") as cursor:
                table_length = (await cursor.fetchone())[0]

        try:
            msg = await ctx.send(
                f"**Language**: {language}\n**Date**: {date}\n**Index**: {index}\n```{chatmsg}```")
            await self.add_reaction(ctx, msg, table_length)
        except Exception as err:
            await ctx.send(err)
            await msg.clear_reactions()


    @commands.cooldown(1, 3)
    @commands.command(aliases=["get"])
    async def getuser(self, ctx, player: fix_username, language: str, limit=10):
        """
            Get player last messages
        """
        conn = sqlite3.connect("./Logs/Chatlogs.db")
        c = conn.cursor()
        messages = c.execute(f"SELECT message FROM {language} WHERE username=? COLLATE NOCASE", (player,)).fetchall()

        async with aiosqlite.connect("./Logs/Chatlogs.db") as conn:
            async with conn.execute(f"SELECT message FROM {language} WHERE username=? COLLATE NOCASE", (player,)) as cursor:
                if limit < 0:
                    messages = (await cursor.fetchall())[:abs(limit)]
                    messages.reverse()
                else:
                    messages = (await cursor.fetchall())[-limit:]

        if len(messages) < 1:
            await ctx.send(f"Can't find messages of {player}")
            return
        
        chatmsg = "```"
        for message in reversed(messages):
            chatmsg += f"{player}:{''.join(message)} \n"
        chatmsg += "```"

        try:
            await ctx.send(content=chatmsg)
        except Exception as err:
            await ctx.send(content=err)


    @commands.cooldown(1, 3)
    @commands.command()
    async def search(self, ctx, word: add_percent, language: str, limit: int=10):
        """
            Search word in logs
        """

        async with aiosqlite.connect("./Logs/Chatlogs.db") as conn:
            async with conn.execute(f"SELECT * FROM {language} WHERE message LIKE ? LIMIT {limit}", (word,)) as cursor:
                messages = await cursor.fetchall()

        if len(messages) < 1:
            await ctx.send(f"Can't find message contains {word}")
            return

        chatmsg = "```"
        for message in messages:
            index, hour, username, message, date = message # assign stuff of message
            chatmsg += f"{hour} {username}:{message} \n"
        chatmsg += "```"

        try:
            await ctx.send(content=chatmsg)
        except Exception as err:
            await ctx.send(content=err)


    @commands.cooldown(1, 3)
    @commands.command()
    async def stats(self, ctx, player: fix_username, language: str):
        """
            Stats of player based on chat logs
        """

        async with aiosqlite.connect("./Logs/Chatlogs.db") as conn:
            async with conn.execute(f"SELECT * FROM {language} WHERE username=? COLLATE NOCASE", (player,)) as cursor:
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


def setup(bot):
    bot.add_cog(Chat(bot))
