import json
import discord
import timeago
from datetime import datetime
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageColor
from matplotlib import pyplot as plt
from matplotlib.text import Annotation
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.font_manager import FontProperties
from bs4 import BeautifulSoup
from aiohttp import ClientSession
from discord.ext import commands


class osu(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.intervals = (
            ('weeks', 604800),  # 60 * 60 * 24 * 7
            ('days', 86400),  # 60 * 60 * 24
            ('hours', 3600),  # 60 * 60
            ('minutes', 60),
            ('seconds', 1),
        )


    def write_to_background(self, img, text_corner, text, font="Torus-SemiBold.otf", font_size=24, align="left", fill=None, center=False):
        font = ImageFont.truetype(f"./Stuff/{font}", font_size)
        draw = ImageDraw.Draw(img)
        if center:
            w, h = font.getsize(text)
            draw.text(((770-w)/2, ((170-h)/2)-12), text, font=font, align=align, fill=fill, stroke_fill=None)
            return
        draw.text(text_corner, text, font=font, align=align, fill=fill, stroke_fill=None)


    async def user_details_website(self, user_id):
        async with ClientSession() as session:
            async with session.get(f"https://osu.ppy.sh/users/{user_id}") as resp:
                if not resp.status == 200:
                    return False

                soup = BeautifulSoup(await resp.text(), "html.parser")
                user_info = json.loads(soup.find(id="json-user").string)
                return user_info


    @commands.command(aliases=["grp"])
    @commands.cooldown(1, 2)
    async def graph(self, ctx, *player):
        players = [player.lower() for player in player]
        players = list(set(players))

        if len(players) > 5:
            await ctx.send("Given players are too much max limit is 5")
            return

        for player in players:
            user_info = await self.user_details_website(player)
            if not user_info:
                await ctx.send("Can't find player")
                return

            rank_history = user_info["rankHistory"]["data"]
            length_rank_history = [*range(len(rank_history))]

            play_counts = [play["count"] for play in user_info["monthly_playcounts"]][-3:]
            length_play_counts = [*range(len(play_counts))]

            fig = plt.figure(figsize=(10, 2))

            plt.tight_layout(pad=0.05)
            fig.set_facecolor("#2a2226")
            plt.gca().set_facecolor("#2a2226")
            plt.axis("off")
            
            ax1 = fig.add_axes([.1, .1, .80, .80], label="Rank History")
            ax1.axis("off")
            ax1.invert_yaxis()
            ax1.plot(length_rank_history, rank_history, linewidth=3, color="#ffcc22")  # Rank plot

            ax2 = fig.add_axes([.1, .1, .80, .80], label="Play Count", frame_on=False)
            ax2.axis("off")
            ax2.plot(length_play_counts, play_counts, linewidth=3, color="#4287f5")  # Play Count plot

            style = {
                "size": 10,
                "color": "#267aff",
                "fontweight": "bold"
            }
            for index, value in enumerate(play_counts):
                ax2.text(index, value+6, str(value), **style)

            sio = BytesIO()
            canvas = FigureCanvas(plt.gcf())
            canvas.print_png(sio)

            image_binary = sio.getvalue()
            graph_img = Image.open(BytesIO(image_binary)).convert("RGBA")
            graph_img = graph_img.crop((120, 10, 890, 180))

            # Write rank to left bottom or up
            txt = Image.new("RGBA", graph_img.size, (255, 255, 255, 0))
            self.write_to_background(txt, (7, 10), f"#{user_info['statistics']['rank']['global']}",
                                         font="BebasNeue-Regular.ttf",font_size=150, fill=(0, 0, 0, 70), center=True)
            graph_img = Image.alpha_composite(graph_img, txt)

            with BytesIO() as image_binary:
                graph_img.save(image_binary, "png")
                image_binary.seek(0)
                await ctx.send(content=f"Graph for {user_info['username']} | :blue_circle: :Play Count :yellow_circle: :Rank",
                               file=discord.File(fp=image_binary, filename=f"{player}_graph.png"))
                plt.close()


    def display_time(self, seconds, granularity=2):
        result = []

        for name, count in self.intervals:
            value = seconds // count
            if value:
                seconds -= value * count
                if value == 1:
                    name = name.rstrip('s')
                result.append("{} {}".format(value, name))
        return ', '.join(result[:granularity])


    def return_time_ago(self, date_muted):
        date_muted_obj = datetime.strptime(date_muted[:-9], "%Y-%m-%dT%H:%M")

        return timeago.format(date_muted_obj)


    @commands.command(aliases=["silence"])
    async def mute(self, ctx, player):
        player = player.replace("_", " ").replace(" ", "_")

        user_details = await self.user_details_website(player)
        if not user_details:
            await ctx.send(f"{player} oyuncusunu bulamadım :pensive:")
            return

        embed = discord.Embed()
        embed.set_author(name=f"{user_details['username']}'s mute stats",
                            icon_url=f"https://a.ppy.sh/{user_details['id']}")
        embed.add_field(name="Muted rn", value=user_details["is_silenced"], inline=False)
        for mutes in user_details["account_history"]:
            embed.add_field(name=f"{mutes['description']} | {self.return_time_ago(mutes['timestamp'])}",
                            value=f"Length: {self.display_time(mutes['length'])}")

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(osu(bot))
