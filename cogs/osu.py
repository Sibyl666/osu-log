import json
import discord
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageColor
from matplotlib import pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from bs4 import BeautifulSoup
from aiohttp import ClientSession
from discord.ext import commands


class osu(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


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
            await ctx.send("Çok player veriyon azalt :pensive:")
            return

        for player in players:
            user_info = await self.user_details_website(player)
            if not user_info:
                await ctx.send("Oyuncuyu bulamadım :pensive:")
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


def setup(bot):
    bot.add_cog(osu(bot))
