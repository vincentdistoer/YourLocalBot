import discord
import asyncio
import time
import datetime

from typing import Union, Optional
from discord.ext.commands import Greedy
from discord.ext import commands
from utils import checks
from utils import errors
import typing
class CallFramework:
    def __init__(self, bot):
        self.bot = bot
    
    def thin(self):
        bot_channels = list(self.bot.get_all_channels())
        bot_can = []
        for x in bot_channels:
            if dict(x.permissions_for(x.guild.me))['send_messages']:
                bot_can.append(x)
        return bot_can

    async def find_hits(self, ctx, inp: Union[str, int, discord.TextChannel]):
        if isinstance(inp, str):  # big fat nerd
            bot_can = self.thin()
            toret = []
            for x in bot_can:
                if x.name.lower() in inp:
                    toret.append(x)
            return toret
        elif isinstance(inp, int):
            x = self.bot.get_channel(inp)  # straight foward
            return [x]
        else:
            return [inp]  # ye wot mate
    
    async def resolve_response(self, ctx, *, response: str, stuff):
        ns = None
        for c in stuff:
            if c in await self.find_hits(ctx, c.name):
                ns = c
                return ns
        else:
            return None 

    async def get_dest_channel(self, ctx, *, response: str):
        """returns channel object for do_call"""
        x = self.thin()
        y = await self.find_hits(ctx, x)
        z = await self.resolve_response(ctx, response=response, stuff=y)
        if isinstance(z, discord.TextChannel):
            return z
        else:
            raise errors.NotFound

    async def do_call(self, ctx, channel: discord.TextChannel):
        num = 0
        phone_num = ""
        for x in str(channel.id):
            if num == 5:
                num += 1
                phone_num += ' ' + x
                continue
            else:
                num += 1
                phone_num += x
        caller = await ctx.send(f"Calling `{phone_num}` \U0000260e")
        async with ctx.channel.typing():
            x = "Ring ring! {ctx.author} is calling from {ctx.channel.id!}! react with \U0001f4de to answer!".format(ctx=ctx)
            rec = await channel.send(x)
            await rec.add_reaction('\U0001f4de')
            def c(r, u):
                return r.message.id == rec.id and str(r.emoji) == '\N{TELEPHONE RECEIVER}' and not u.bot
            try:
                reaction, user = await self.bot.wait_for('reaction_add', check=c, timeout=40)
            except asyncio.TimeoutError:
                await caller.edit(content=f"\U0001f4f5 {phone_num} didn't pick up in time.")
                await rec.edit(content=f"\U0001f4f5 You missed a call from {ctx.author}!")
                await rec.clear_reactions()
                return False
            await caller.edit(content=f"**You are now connected with {user}! say hi!**\n*To end the call, simple say \"End Call\"*")
            await rec.edit(content=f"**You are now connected with {ctx.author}! say hi!**\n*To end the call, simple say \"End Call\"*")
        while True:
            def ch(m):
                return m.author in [user, ctx.author] and m.channel in [ctx.channel, channel]
            m = await self.bot.wait_for('message', check=ch)
            if 'end call' in m.content.lower():
                await rec.edit(content=f"**{m.author} has ended the call.**")
                await caller.edit(content=f"**{m.author} has ended the call.**")
                await rec.channel.send(f"**{m.author} has ended the call.**")
                await caller.channel.send(f"**{m.author} has ended the call.**")
                break
            nc = m.clean_content.replace('/', '\u200b/')
            if m.channel == channel:
                await ctx.channel.send(f"{m.author.name}: {nc}")
                await asyncio.sleep(1)
            else:
                await channel.send(f"{m.author.name}: {nc}")
        return
class Call(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.cf = CallFramework(bot)
        self.on_call = 0
        self.extras = 0
        self.lines = int(str(round(len(self.bot.get_guild(486910899756728320).members)) * 10)[0]) - 5


    @commands.group(name="call", invoke_without_command=True)
    @commands.guild_only()
    @commands.cooldown(1, 300, commands.BucketType.user)
    @commands.cooldown(1, 600, commands.BucketType.guild)
    async def _call(self, ctx, channel: typing.Union[discord.TextChannel, str]):
        """call another server via the disphone!"""
        
        if self.on_call >= self.lines:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send(f"Too many users are on call!\n**Available lines:** {self.lines}\n**How do we get more lines?**: do `y!call getmorelines`.")
        self.on_call += 1
        await self.cf.do_call(ctx, channel)
        self.on_call -= 1
    
    @_call.command(name='init')
    @checks.co_owner()
    async def call_init(self, ctx):
        self.extras = len(await self.bot.dbl_client.get_bot_upvotes())
        self.lines += self.extras
        await ctx.send(self.__init__)
    
    @_call.command()
    async def getmorelines(self, ctx):
        """Get more call lines!"""
        guild = discord.utils.get(ctx.bot.guilds, id=486910899756728320)
        amount = 10 - round((100-self.lines) / 10)
        e = discord.Embed(
            description=f"want to open a new line? Methods:\n[Join this server](https://invite.gg/ebot)\n[Vote for the bot (extra lines, only last for 12h)](https://discordbots.org/bot/558689453573406771/vote)"
        )
        x = f"Current lines: {self.lines}\nMembers until new line: {amount}\nBonus Lines: {self.extras}"
        await ctx.send(x, embed=e)

    @_call.command(name="add-artif-use", aliases=['aau', 'addartifuse', 'addincall'])
    @commands.is_owner()
    async def add_artif_inuse(self, ctx, amount: int = 1):
        """add more calls that are in use"""
        self.on_call += amount
        await ctx.send(f"Now in use: {self.on_call}/{self.lines}")
    
    @_call.command(name="rem-artif-use", aliases=['rau', 'remartifuse', 'remincall'])
    @commands.is_owner()
    async def rem_artif_inuse(self, ctx, amount: int = 1):
        """add more calls that are in use"""
        self.on_call -= amount
        await ctx.send(f"Now in use: {self.on_call}/{self.lines}")

    @_call.command(aliases=['addline'])
    @commands.is_owner()
    async def add_line(self, ctx, amount: int = 1):
        """add a line."""
        self.lines += amount
        await ctx.send(f"Now in use: {self.on_call}/{self.lines}")
    
    @_call.command(aliases=['remline'])
    @commands.is_owner()
    async def rem_line(self, ctx, amount: int = 1):
        """add a line."""
        self.lines -= amount
        await ctx.send(f"Now in use: {self.on_call}/{self.lines}")


def setup(bot):
    bot.add_cog(Call(bot))
