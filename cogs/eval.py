from discord.ext import commands
import asyncio
import traceback
import discord
import inspect
import textwrap
from contextlib import redirect_stdout
import io
import copy
from typing import Union
from utils.page import pagify
from utils.escapes import *
import os
import random
import time

# to expose to the eval command
import datetime
from collections import Counter
# source command
from inspect import getsource
from utils import checks
class Eval(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_result = None
        self.permitted = [421698654189912064]
        self.success = 'success:522078924432343040'
        self.loading = 'a:loading20:553253741311295498'
        self.error = 'fail:522076877075251201'

    def cleanup_code(self, content):
        """Automatically removes code blocks from the code."""
        # remove ```py\n```
        if content.startswith('```') and content.endswith('```'):
            return '\n'.join(content.split('\n')[1:-1])

        # remove `foo`
        return content.strip('` \n')

    @staticmethod
    async def log(ctx: commands.Context, code):
        g = discord.utils.get(ctx.bot.guilds, id=486910899756728320)
        c = discord.utils.get(g.text_channels, name='eval-logs')
        fm = "**{0.name}** (`{0.id}`) used eval!\n```py\n{1}\n```".format(ctx.author, code)
        d = f"Author: {ctx.author} | {ctx.author.id} {f' | {ctx.author.mention}' if ctx.author in g.members else None}" \
            f"\nChannel: {ctx.channel.name} | {ctx.channel.id}\nServer: {ctx.guild.name} | {ctx.guild.id}"
        e = discord.Embed(title="info", description=d, color=discord.Color.blue())
        e.set_author(icon_url=ctx.author.avatar_url, name=ctx.author)
        await c.send(fm, embed=e)

    @commands.command(pass_context=True, hidden=True, name='eval', aliases=['do', 'run'])
    @checks.co_owner()
    async def _eval(self, ctx, *, body: str):
        """Evaluates a code"""
        await self.log(ctx, body)
        await ctx.message.add_reaction(self.loading)
        env = {
            'bot': self.bot,
            'ctx': ctx,
            'channel': ctx.channel,
            'author': ctx.author,
            'guild': ctx.guild,
            'message': ctx.message,
            'command': ctx.command,
            '_': self._last_result,
            'asyncio': asyncio,
            'discord': discord,
            'datetime': datetime,
            'os': os,
            'random': random,
            'time': time
        }

        env.update(globals())

        body = self.cleanup_code(body)
        stdout = io.StringIO()

        to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'

        try:
            exec(to_compile, env)
        except Exception as e:
            await ctx.message.clear_reactions()
            await ctx.message.add_reaction(self.error)
            for page in pagify(f'{e.__class__.__name__}: {e}'.replace('`', '\u200b`')):
                await ctx.send(f'```py\n{page}\n```')
            return

        try:
            func = env['func']
        except:
            pass
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception as e:
            value = stdout.getvalue()
            try:
                await ctx.message.clear_reactions()
            except:
                pass
            await ctx.message.add_reaction(self.error)
            for p in pagify(f'{value}{traceback.format_exc()}'.replace('`', '\u200b`')):
                await ctx.send(f'```py\n{p}\n```')
        else:
            value = stdout.getvalue()
            try:
                await ctx.message.clear_reactions()
            except:
                pass
            try:
                await ctx.message.add_reaction(self.success)
            except:
                pass
            if ret is None:
                if value:
                    for p in pagify(value.replace('`', '\u200b`')):
                        await ctx.send(f'```py\n{p}\n```')
                else:
                    await ctx.send('No Value to return.', delete_after=2.5)
            else:
                self._last_result = ret
                for p in pagify(f'{value}{ret}'.replace('`', '\u200b`')):
                    await ctx.send(f'```py\n{p}\n```')

    @commands.command(hidden=True)
    @commands.is_owner()
    async def sudo(self, ctx, who: Union[discord.Member, discord.User], *, command: str):
        """Run a command as another user."""
        msg = copy.copy(ctx.message)
        msg.author = who
        msg.content = ctx.prefix + command
        new_ctx = await self.bot.get_context(msg, cls=type(ctx))
        await self.bot.invoke(new_ctx)

    @commands.command()
    @checks.co_owner()
    async def source(self, ctx, *, command: str):
        """Get the source code of a command!"""
        self.bot.owner = discord.utils.get(self.bot.users, id=self.bot.owner_id)
        eek = self.bot.owner
        async def _c(msg):
            def check(r):
                return r.author in [ctx.author, eek] and r.channel == ctx.channel and r.content.lower() == 'delete'
            r = await self.bot.wait_for('message', check=check)
            await msg.delete()
        async def do_mass(msg: list):
            def check(r):
                return r.author == ctx.author and r.channel == ctx.channel and r.content.lower() == 'delete'
            r = await self.bot.wait_for('message', check=check)
            for m in msg:
                await m.delete()
        command = self.bot.get_command(command)
        if command is None:
            return await ctx.send('no command found')
        source = getsource(command.callback).replace('`', '\u200B`\u200B')
        if len(source) < 1750:
            msg = await ctx.send("```py\n" + source + "\n```")  #1
            await _c(msg)
        else:
            messages = []
            async with ctx.channel.typing():
                for page in pagify(source, page_length=1750):
                    X = await ctx.send(f"```py\n{page}\n```")  # 2
                    await asyncio.sleep(1)
                    messages.append(X)
            await do_mass(messages)


def setup(bot):
    bot.add_cog(Eval(bot))
