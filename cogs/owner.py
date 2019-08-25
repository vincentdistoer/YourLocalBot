import discord, asyncio, os, datetime, psutil, typing, traceback
from discord.ext import commands
from utils.page import pagify
from discord import User
from typing import Optional
# get custom checks
import utils.checks as checks
import dbl

class OwnerControl(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjU1ODY4OTQ1MzU3MzQwNjc3MSIsImJvdCI6dHJ1ZSwiaWF0IjoxNTYwOTA3MzQwfQ.mz8fJihyMJq5e6Pyw44pH0jiZBV3MOxvZPO8kkUAN28'
        self.dblpy = dbl.Client(self.bot, self.token)
        self.bot.dbl_client = self.dblpy

    @commands.command(name='o.info')
    @checks.co_owner()
    async def oooinfo(self, ctx):
        o = await self.bot.fetch_user(421698654189912064)
        url = 'http://discord.gg/mNV6azN'
        loaded = 0
        cogs = 11
        loadedcogs = 0
        musage = psutil.virtual_memory().percent
        corenum = 0
        forefmt = ""
        cpu_usage = psutil.cpu_percent(interval=None, percpu=True)
        for corepercent in cpu_usage:
            corenum += 1
            forefmt += f"Core {corenum}: {corepercent}%\n"
        e = discord.Embed(title="My info!", color=self.bot.user.color, timestamp=datetime.datetime.utcnow())
        e.url = url
        e.add_field(name="Users:", value=len(self.bot.users))
        cc = 0
        files = 0
        for s in self.bot.guilds:
            cc += len(s.channels)
        for d in os.listdir():
            files += 1
        e.add_field(name="Channels:", value=cc)
        e.add_field(name="Guilds:", value=len(self.bot.guilds))
        e.add_field(name="Total executed commands:", value="Null")
        e.add_field(name="Owner:", value=o)
        e.add_field(name="Memory usage:", value=f"{musage}%")
        e.add_field(name="CPU usage:", value=forefmt)
        e.add_field(name="Total files:", value=files)
        await ctx.send(embed=e)

    @commands.command()
    @checks.co_owner()
    async def memtrack(self, ctx, length: int = 10):
        x = await ctx.send('tracking...')
        await asyncio.sleep(5)
        results = []
        done = 0
        for i in range(length):
            done += 1
            musage = psutil.virtual_memory().percent
            if done == 5:
                final = f"{str(musage)}%\n"
            await x.edit(content=str(musage) + "%")
            results.append(musage)
            await asyncio.sleep(1)
        ffmt = ""
        for j in results:
            ffmt += f" {j} "
        return await x.edit(content=str(final) + 'Final results: `' + ffmt + '`.')

    @commands.command()
    @checks.co_owner()
    async def unload(self, ctx, *cogs: str):
        """unload a cog"""
        try:
            for cog in cogs:
                self.bot.unload_extension('cogs.' + cog.replace('cogs.', '').replace('.py', ''))
                await ctx.send(f"unloaded {cog}")
        except:
            for p in pagify(traceback.format_exc()):
                await ctx.send(f"```py\n{p}\n```")


    @commands.command()
    @checks.co_owner()
    async def rcd(self, ctx, command: str, user: Optional[User], channel: Optional[discord.TextChannel]):
        """Reset a command cooldown"""
        _ctx = ctx
        if user is not None:
            ctx.author = user
        if channel is not None:
            ctx.channel = channel
        self.bot.get_command(command).reset_cooldown(ctx)
        await _ctx.send("Success!")


    @commands.command()
    async def post(self, ctx):
        try:
            await self.dblpy.post_guild_count()
            await ctx.send(('Posted server count ({})'.format(self.dblpy.guild_count())))
        except Exception as e:
            await ctx.send(f"Error: {e}")

    @commands.Cog.listener()
    async def on_dbl_vote(self, data):
        if isinstance(data, dict):
            if data['bot'] == self.bot.user.id:
                c = self.bot.get_channel(572792559705915402)
                u = await self.bot.fetch_user(data['user'])
                if data['type'] == 'test':
                    await c.send(embed=discord.Embed(title="Upvote-test",
                    description=u.name))
                else:
                    g = self.bot.get_guild(486910899756728320)
                    if u in g.members:
                        u = discord.utils.get(g.members, id=u.id) # get member instance
                        r = g.get_role(576468526152286218)
                        await u.add_roles(r)
                        await c.send(
                            u.mention,
                            embed=discord.Embed(
                                title=f"{u.name} just upvoted!",
                                descrption="Thank you {.name} for upvoting!",
                                color=discord.Color.blurple(),
                                timestamp=datetime.datetime.utcnow()
                            )
                        )
                        await asyncio.sleep(43200)
                        await u.remove_roles(r)
                    else:
                        await c.send(embed=discord.Embed(
                                title=f"{u.name} just upvoted!",
                                descrption="Thank you {.name} for upvoting!",
                                color=discord.Color.blurple(),
                                timestamp=datetime.datetime.utcnow()
                            ))
def setup(bot):
    bot.add_cog(OwnerControl(bot))
