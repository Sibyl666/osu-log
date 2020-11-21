import socket
import time
import os
import re
import asyncio
import logging
import aiosqlite
from datetime import datetime
from pytz import timezone
from dotenv import load_dotenv
load_dotenv()

zone = timezone("Asia/Istanbul")
strp_format = "%H:%M"

# IRC stuff
server = "irc.ppy.sh"
port = 6667
sockt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
channel_list = ['announce', 'arabic', 'balkan', 'bulgarian', 'cantonese', 'chinese', 'ctb', 'czechoslovak', 'dutch', 'english', 'filipino', 'finnish', 'french', 'german', 'greek', 'hebrew', 
'help', 'hungarian', 'indonesian', 'italian', 'japanese', 'korean', 'malaysian', 'modhelp', 'modreqs', 'osu', 'osumania', 'polish', 'portuguese', 'romanian', 'russian', 'skandinavian', 'spanish', 'taiko', 'thai', 'turkish', 'ukrainian', 'videogames', 'vietnamese']


# Logging
logging.basicConfig(filename="logs.log")

connected = False


def connect():
    global connected
    global sockt
    while not connected:
        try:
            sockt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sockt.connect((server, port))
            sockt.send(f"PASS {os.getenv('ircpass')} \n".encode())
            sockt.send(b"NICK Sibyl \n")
            sockt.send(b"USER Sibyl Sibyl Sibyl :Sibyl \n")

            for channel in channel_list:
                sockt.send(f"JOIN #{channel} \n".encode())

            connected = True
            logging.info("Connected")
            break
        except:
            logging.error("Reconnect error")
            time.sleep(10)
            continue


connect()
async def main():
    global connected
    while connected:
        try:
            data = sockt.recv(4069).decode("utf-8", errors='ignore')
        except:
            logging.error("Timeout error")
            continue

        if len(data) == 0:
            connected = False
            logging.error("Length Zero")
            connect()
            continue

        for message in data.splitlines():
            if "PING" in message:
                sockt.send(b"PONG :cho.ppy.sh \n")
                logging.info("Ping")
                continue

            splitted_message = message.split(":")
            try:
                if not "PRIVMSG" in splitted_message[1]:
                    continue

                match = re.search(r":(?P<username>.{1,15})!cho@ppy.sh PRIVMSG (?P<table>#[^\s]+) (?P<message>:.*)", message)
                print(match)
                if match:
                    username, table, message = match.groups()
                    table = table.replace("#", "")
                    message = message.replace(":", " ", 1)

                    now = datetime.utcnow()
                    hour = now.strftime("%H:%M")
                    date = now.strftime("%Y-%m-%d")
                
                    try:
                        async with aiosqlite.connect("../Logs/Chatlogs.db") as conn:
                            async with await conn.execute(f"INSERT INTO {table} (hour, username, message, date) VALUES (?,?,?,?)", (hour, username, message, date)) as cursor:
                                await conn.commit()
                                logging.info(f"Added {match}")
                    except Exception as err:
                        print(match)
                        print(username, table, message, now, hour, date)
                        logging.exception("Cant add to database")

            except:
                continue


if __name__ == "__main__":
    asyncio.run(main())
