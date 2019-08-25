import asyncio
import logging
import os
import random
import time
import traceback
import typing

import aiohttp
import discord as d
from discord.ext import commands

import utils
from utils import checks
from utils.escapes import *
from utils.page import pagify


class GuilcConverter(commands.Converter):
    async def convert(self, ctx, argument):
        for guild in ctx.bot.guilds:
            if guild.id == argument or guild.name.lower() == str(argument).lower() or argument in [x.id for x in guild.channels] or str(argument).lower().replace(' ', '-') in [x.name for x in guild.channels]:
                try:
                    return guild
                except Exception as E:
                    raise TypeError("IDK what would raise an error in this example but I need to put one here so here it is")
        else:
            raise Exception("NO GUILD FOUND")


logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename='YourLocal.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)
start = time.time()
discord = d
description = 'YLB - a new, revelutionaty multiuse toolbot!'
mm = 500
bot = commands.Bot(command_prefix=commands.when_mentioned_or('ylb ', 'y!', 'Y!'), description=description,
                   case_insensitive=True, activity=discord.Game(name="Booting..."),
                   status=discord.Status.do_not_disturb, owner_id=421698654189912064, help_command=commands.help.DefaultHelpCommand(dm_help=None,
                                                                 dm_help_threshold=1500,
                                                                 no_category="main file"), max_messages=mm)
bot.streaming = None
bot.max_messages = mm
# a b c d e f g h i j k l m n o p q r s t u v w x y z
cogss = [
    'cogs.autorole',
    'cogs.an',
    'cogs.bump',
    'cogs.config',
    'cogs.db',
    'cogs.dev',
    'cogs.eco',
    'cogs.eval',
    'cogs.fun',
    'cogs.help',
    'jishaku',
    'cogs.main',
    'cogs.mod',
    'cogs.misc',
    'cogs.owner',
    'cogs.tickets',
    'cogs.tsl'
]  # lets go priority order

bot.global_lockout = False


def is_owner():
    async def someshitvarname(ctx):
        if ctx.author.id == ctx.bot.owner_id:
            return True
    return commands.check(someshitvarname)


@bot.event
async def on_ready():
    print("Logged in!")
    bot.finished = round(time.time() - start, 3)
    await bot.change_presence(activity=discord.Game("Loading..."), status=discord.Status.idle)
    cogs = 0
    for i in cogss:
        try:
            bot.load_extension(i)
            cogs += 1
        except:
            traceback.print_exc()
            continue
    bot.loaded_c0gs = cogs
    print('\n'*100)
    print(f"loaded {cogs} cogs.")
    print(f"Ok, letsa go!\nGUILDS: {len(bot.guilds)}\nUsers: {len(bot.users)}\nBoot Time: {bot.finished}")
    co = [f"along side {len(bot.guilds)} guilds!", f"along side {len(bot.users)} users!"]
    await bot.change_presence(activity=discord.Game(random.choice(co)), status=discord.Status.online)
    await asyncio.sleep(10)
    print(f'https://discordapp.com/oauth2/authorize?client_id={bot.user.id}&permissions=0&scope=bot')


@bot.group(aliases=['reload', 'sex'], invoke_without_command=True)
@checks.co_owner()
async def r(ctx, cog):
    """reload a cog."""
    bot.loaded_c0gs = 9999999
    cog = cog.replace('cogs.', '').replace('.py', '')
    s = time.time()
    try:
        bot.reload_extension(f'cogs.{cog}')
        e = time.time()
        ot = round(e - s, 2)
        await ctx.send(f'\U0001f44c reloaded {cog} in {ot} seconds.')
    except commands.ExtensionNotLoaded:
        bot.load_extension(f'cogs.{cog}')
        e = time.time()
        ot = round(e - s, 2)
        await ctx.send(f'\U0001f44c loaded {cog} in {ot} seconds.')
    except commands.ExtensionNotFound:
        await ctx.send(f'\U0000270b {cog} was not found!')
    except Exception as e:
        for page in pagify(e, page_length=1800):
            await ctx.send(f'```py\n{page}\n```')

@r.command()
@checks.co_owner()
async def all(ctx):
    s = time.time()
    for cog in cogss:
        print(cog)
        if cog.lower() == 'cogs.an':
            continue
        try:
            bot.reload_extension(f'{cog}')
            e = time.time()
            ot = round(e - s, 2)
            await ctx.send(f'\U0001f44c reloaded {cog} in {ot} seconds.')
        except commands.ExtensionNotLoaded:
            bot.load_extension(f'{cog}')
            e = time.time()
            ot = round(e - s, 2)
            await ctx.send(f'\U0001f44c loaded {cog} in {ot} seconds.')
            
        except commands.ExtensionNotFound:
            await ctx.send(f'\U0000270b {cog} was not found!')
        except Exception as e:
            for page in pagify(e, page_length=1800):
                await ctx.send(f'```py\n{page}\n```')
        await asyncio.sleep(1)

bot.locked_out = {399587357931601921: "Homo slurs, gc spam, staff abuse\nLength: Perm."}

@bot.check
async def not_locked_out(ctx):
    if ctx.author.id == bot.owner_id or ctx.command.name == 'islocked':
        #await ctx.send("owner")
        return True 
    else:
        if bot.global_lockout is True:      
            return False
        else:
            return ctx.author.id not in list(bot.locked_out)


@bot.group(invoke_without_command=True, aliases=['blacklist', 'bl'])
@checks.co_owner()
async def lock(ctx, user: typing.Union[int, discord.User], *, reason: typing.Optional[str]='No reason provided.', time: int=86400):
    if isinstance(user, discord.User):
        user = user.id
    if user not in bot.locked_out:
        bot.locked_out[user] = reason
    final = "Locked users:\n```\n"
    for a, b in enumerate(list(bot.locked_out), start=1):
        final += f"{a}: {b}\n"
    final += f"```\nGlobal Lockout Mode: {bot.global_lockout}"
    await ctx.send(final)
    if time == 0:
        return
    await asyncio.sleep(time)
    await ctx.author.send("removed {}".format(user))
    try:
        del bot.locked_out[user]
    except KeyError:
        return


@lock.command(name="global")
@checks.co_owner()
async def _global(ctx, *, reason: str=None):
    """Lock the bot globally"""
    bot.global_lockout=True
    final = "Locked users:\n```\n"
    for a, b in enumerate(list(bot.locked_out),start=1):
        final += f"{a}: {b}\n"
    final += f"```\nGlobal Lockout Mode: {bot.global_lockout}"
    await ctx.send(final)


@bot.group(invoke_without_command=True)
@checks.co_owner()
async def unlock(ctx, user: typing.Union[int, discord.Member]):
    if isinstance(user, discord.Member):
        user = user.id
    if user in bot.locked_out:
        del bot.locked_out[user]
    final = "Locked users:\n```\n"
    for a, b in enumerate(list(bot.locked_out), start=1):
        final += f"{a}: {b}\n"
    final += f"```\nGlobal Lockout Mode: {bot.global_lockout}"
    await ctx.send(final)


@unlock.command(name="global")
@checks.co_owner()
async def __global(ctx):
    """Globally allow bot."""
    bot.global_lockout=False
    final = "Locked users:\n```\n"
    for a, b in enumerate(list(bot.locked_out), start=1):
        final += f"{a}: {b}\n"
    final += f"```\nGlobal Lockout Mode: {bot.global_lockout}"
    await ctx.send(final)


@bot.command(hidden=True)
async def islocked(ctx, user: discord.User):
    """Check if a someone is locked"""
    if user.id in list(bot.locked_out):
        await ctx.send(f'True\nReason: {bot.locked_out[user.id]}')
    else:
        await ctx.send('False')


@bot.command(hidden=True)
@commands.is_owner()
async def stream(ctx, arg: bool):
    bot.streaming = arg
bot.total_uptime = start
bot.supersecrettokenattr = 'NDIxNjk4NjU0MTg5OTEyMDY0.WFdLZnVR.bmljZSB0cnkuIG5vdCA0IHU='
token= 'NDIxNjk4NjU0MTg5OTEyMDY0.WFdLZnVR.bmljZSB0cnkuIG5vdCA0IHU='


async def deceit():
    bot.session = aiohttp.ClientSession()
    await bot.wait_until_ready()
    while not bot.is_closed():
        if bot.streaming:
            await bot.change_presence(activity=discord.Streaming(name="My developer is live!", url="https://twitch.tv/eekimplays"))
        else:
            sta = [discord.Game(name=f"with {len(bot.commands)} commands!"),
               discord.Activity(type=discord.ActivityType.watching, name=f"over {len(bot.guilds)} guilds!"),
               discord.Activity(type=discord.ActivityType.listening, name=f"to {len(bot.users)} users!")]
            await bot.change_presence(activity=random.choice(sta))
        await asyncio.sleep(60)


bot.loop.create_task(deceit())


@bot.event
async def on_disconnect():
    print(f"[[info]] bot disconnect handled - closing 'asession'...")
    await bot.session.close()
    print('success!')


bot.run(token)
