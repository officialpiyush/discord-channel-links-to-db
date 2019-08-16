import re
import time
import asyncio
import discord
from discord.ext import commands

from rethinkdb import RethinkDB

r = RethinkDB()
r.set_loop_type("asyncio")

regex = re.compile(
    r'^(?:http|ftp)s?://'  # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain
    r'localhost|'  # localhost
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # or ip
    r'(?::\d+)?'  # optional port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)

reg = 'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'


class SaveToDB(commands.Cog):
    def __init__(self, bot):
        self.bot: discord.Client = bot

    @commands.command()
    async def save(self, ctx: commands.Context, channel: discord.TextChannel):
        connection = await r.connect("localhost", 28015)

        dbs = await r.db_list().run(connection)
        if "acedesyn" not in dbs:
            await r.db_create("acedesyn").run(connection)

        tables = await r.db("acedesyn").table_list().run(connection)

        if str(channel.id) in tables:
            await r.db("acedesyn").table_drop(str(channel.id)).run(connection)
            await r.db("acedesyn").table_create(str(channel.id)).run(connection)
        else:
            await r.db("acedesyn").table_create(str(channel.id)).run(connection)

        messages = await channel.history(limit=None, oldest_first=True).flatten()

        counter = 0
        total = len(messages)
        m: discord.Message = await ctx.send(f"Saved {str(counter)} links from {str(total)} messages")
        for message in messages:
            message: discord.Message = message

            urls = re.findall(reg, message.content.replace("<", "").replace(">", ""))
            if urls and urls[0]:
                link = urls[0]
                await r.db("acedesyn").table(str(channel.id)).insert({
                    "author": {
                        "id": str(message.author.id),
                        "username": f"{message.author.name}#{message.author.discriminator}"
                    },
                    "message_id": str(message.id),
                    "link": str(link),
                    "content": str(message.content.replace("<", "").replace(">", "")),
                    "message_link": str(message.jump_url),
                    "timestamp": str(message.created_at),
                    "inserted_timestamp": str(time.time())
                }).run(connection)
                counter = counter + 1
                await m.edit(content=f"Saved {str(counter)} links from {str(total)} messages")


def setup(bot):
    bot.add_cog(SaveToDB(bot))
