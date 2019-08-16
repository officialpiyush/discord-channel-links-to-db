from discord.ext import commands

bot = commands.Bot(command_prefix="!!")

initial_extensions = ["cogs.SaveToDB"]

if __name__ == '__main__':
    for extension in initial_extensions:
        bot.load_extension(extension)


@bot.event
async def on_ready():
    print(f'Successfully logged in and booted...!')

bot.run("")
