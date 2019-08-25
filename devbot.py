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

logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename='YourLocal.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)
start = time.time()
discord = d
mm = 9999999
description = 'YLB - a new, revelutionaty multiuse toolbot!'
bot = commands.Bot(command_prefix=commands.when_mentioned_or('d!', 'dev'), description=description,
                   case_insensitive=True, activity=discord.Game(name="Booting..."),
                   status=discord.Status.do_not_disturb, owner_id=421698654189912064, help_command=commands.help.DefaultHelpCommand(dm_help=None,
                                                                 dm_help_threshold=1500,
                                                                 no_category="main file"), max_messages=mm)
bot.max_messages = mm
token='' #main token
cogss = [
    'cogs.main',
    'cogs.owner',
    'cogs.an',
    'cogs.bump',
    'cogs.db',
    'cogs.eval',
    'cogs.dev',
    'cogs.mod',
    'cogs.tickets',
    'cogs.misc',
    'cogs.help',
    'cogs.call'
]  # lets go priority order
bot.cogss = cogss
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
    logger.info(f"loaded {bot.loaded_c0gs} cogs.")
    print('\n'*100)
    print(f"loaded {cogs} cogs.")
    print(f"Ok, letsa go!\nGUILDS: {len(bot.guilds)}\nUsers: {len(bot.users)}\nBoot Time: {bot.finished}")
    co = [f"along side {len(bot.guilds)} guilds!", f"along side {len(bot.users)} users!"]
    await bot.change_presence(activity=discord.Game(random.choice(co)), status=discord.Status.online)
    await asyncio.sleep(10)
    print(f'https://discordapp.com/oauth2/authorize?client_id={bot.user.id}&permissions=0&scope=bot')

loaded = ""
@bot.group(aliases=['reload', 'sex'], invoke_without_command=True)
@checks.co_owner()
async def r(ctx, *cogs: str):
    """reload a cog."""
    loaded=""
    bot.loaded_c0gs = -1
    s = time.time()
    m = await ctx.send(f"Re/loading {len(cogs)}/{len(cogss)} cogs <a:typing:599183913889431603>")
    for cog in cogs:
        cog = cog.replace('cogs.', '').replace('.py', '')
        try:
            bot.reload_extension(f'cogs.{cog}')
            e = time.time()
            ot = round(e - s, 2)
            loaded += f'\U0001f44c reloaded {cog} in {ot} seconds.'
        except discord.ext.commands.errors.ExtensionNotFound:
            loaded += f'\U0000270b {cog} was not found!'
        except commands.ExtensionNotLoaded:
            bot.load_extension(f'cogs.{cog}')
            e = time.time()
            ot = round(e - s, 2)
            loaded += f'\U0001f44c loaded {cog} in {ot} seconds.'
        except Exception as e:
            for page in pagify(traceback.format_exc(), page_length=1800):
                await ctx.send(f'```py\n{page}\n```', delete_after = 10)
            loaded += f"\U0000270b {cog} failed to load"
            traceback.print_exc()
            await asyncio.sleep(5)
        continue
    await m.edit(content=loaded)


@r.command()
@checks.co_owner()
async def all(ctx):
    s = time.time()
    for cog in cogss:
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
            for page in pagify(str(e), page_length=1800):
                await ctx.send(f'```py\n{page}\n```')
        await asyncio.sleep(1)

bot.locked_out = {}

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


@bot.group(invoke_without_command=True)
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
bot.total_uptime = start
bot.supersecrettokenattr = token
token='NTY1NTUxODEwODAzMTM4NTYw.XRzmLw.tc8NTClzaLUtpCVJXywsWXUuNpY'
@bot.event
async def on_disconnect():
    logger.warn(f"bot disconnect handled - closing 'asession'...")
    await bot.asession.close()
    print('success!')
async def deceit():
    await bot.wait_until_ready()
    while not bot.is_closed():
        sta = [discord.Game(name=f"with {len(bot.commands)} commands!"), 
               discord.Activity(type=discord.ActivityType.watching, name=f"over {len(bot.guilds)} guilds!"),
               discord.Activity(type=discord.ActivityType.listening, name=f"to {len(bot.users)} users!")]
        await bot.change_presence(activity=random.choice(sta))
        await asyncio.sleep(60)
bot.loop.create_task(deceit())

@bot.event
async def on_connect():
    bot.asession = aiohttp.ClientSession()
    logger.info('Started client session and connected to discord.')
try:
    bot.run(token)
except:
    # fatal
    print('fatal error.')
    logging.shutdown()
