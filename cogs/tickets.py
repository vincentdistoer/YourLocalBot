import discord
import os
import datetime
import asyncio
import random
import time as _time

from utils import checks
from utils.formatting import Humanreadable
from utils.escapes import *
from discord.ext import commands
from random import randint


class TicketSystem(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.dtf = "%I:%M %p @ %d/%m/%Y %Z"

    @commands.command()
    @checks.support_guild()
    async def bug(self, ctx, *, info: str):
        """Report a bug"""
        inu = await ctx.send("Checking for open reports...")
        if str(ctx.author.id) in os.listdir('./data/tickets/bugs'):
            await inu.edit(content="ticket already open; finding...")
            for x in ctx.guild.text_channels:
                if x.name.startswith('bug-') and x.name.endswith(str(ctx.author.id)):
                    return await inu.edit(content=f"Please go to {x.mention} first ^_^")
        else:
            await inu.edit(content="Creating ticket")
            fi = open(f'./data/tickets/bugs/{str(ctx.author.id)}', 'w+')
            fi.write(str(ctx.author.id))
            fi.close()
            for x in ctx.guild.categories:
                if x.name == 'tickets':
                    cat = x
                    support_role = discord.utils.get(ctx.guild.roles, name='Support')
                    dev = discord.utils.get(ctx.guild.roles, name='Developer')
                    overwrites = {
                        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                        ctx.guild.me: discord.PermissionOverwrite(read_messages=True),
                        ctx.author: discord.PermissionOverwrite(read_messages=True, send_messages=True,
                                                                embed_links=True,
                                                                attach_files=True),
                        support_role: discord.PermissionOverwrite(read_messages=True, send_messages=True,
                                                                  embed_links=True,
                                                                  attach_files=True)

                    }
                    chan = await cat.create_text_channel(f'bug-{str(ctx.author.id)}', overwrites=overwrites,
                                                         reason=f"Ticket created by {ctx.author}",
                                                         topic=str(ctx.author.id))
                    await chan.send(f"Our {dev.mention}s have been notified about your issue\nif you havent already, please go and "
                                    "check out our status page @ https://ylb.statuspal.io/?lang=en\nINFO:\n"
                                    f"{escape(info, mass_mentions=True, formatting=False, invites=False)}")
                    return await inu.edit(content=f"Please go to {chan.mention} ^_^")

    @commands.command()
    @checks.support_guild()
    @commands.has_any_role('Support', 'Developer')
    async def close(self, ctx, *, reason: str = None):
        """Close the current ticket"""
        await self.closemethod(ctx, reason=reason)

    async def closemethod(self, ctx, *, reason: str = None):
        c = discord.utils.get(ctx.guild.text_channels, name='ticket-logs')
        if ctx.author.id == ctx.author.id:  # True, always.
            case = randint(1, 1000)
            total = 0
            abcdef = await ctx.send("logging.")
            if ctx.channel.name.startswith('bug'):
                c_type = 'bug'
            elif ctx.channel.name.startswith('support'):
                c_type = 'support'
            elif ctx.channel.name.startswith('idea'):
                c_type = 'idea'
            else:
                c_type = None
            if c_type is None:
                return await abcdef.edit(content="Invalid Ticket!")
            if f'{c_type}-{case}.txt' in os.listdir('./data/tickets/logs'):
                case = randint(1000, 2000)
            with open(f'./data/tickets/logs/{c_type}-{case}.txt', 'w+') as file:
                async for message in ctx.channel.history(limit=9999999, oldest_first=True, before=ctx.message):
                    total += 1
                    if len(message.embeds) >= 1 and (message.content is None or message.content == ""):
                        embed = message.embeds[0].to_dict()
                        del embed['type']
                        file.write(f"{message.author.name} {message.created_at.strftime(self.dtf)}:\nEMBED DATA:\n{embed}")
                        continue
                    try:
                        file.write(f"{message.author.name} {message.created_at.strftime(self.dtf)}:\n"
                               f"{message.clean_content}\n\n")
                    except:
                        file.write(f"{message.author.name} {message.created_at.strftime(self.dtf)}:\n"
                                  f"ERROR IN WRITING...\n\n")
                file.close()
            user = discord.utils.get(ctx.guild.members, id=int(ctx.channel.name.strip(f"{c_type}-")))
            await abcdef.edit(content="Logged! closing in `10` seconds. \U0001f44b")
            await asyncio.sleep(10)
            try:
                os.remove(f'./data/tickets/{c_type}/{int(ctx.channel.topic)}')
            except FileNotFoundError:
                pass
            await ctx.channel.delete(reason=f"{c_type} ticket closed.")
            c = discord.utils.get(ctx.guild.text_channels, name='ticket-logs')
            e = discord.Embed(
                title=f"{c_type} ticket closed",
                description=f"**Closed by:** {ctx.author.mention}\n**Closed at:** "
                f"{ctx.message.created_at.strftime(self.dtf)}\n**Total messages:** {total}\n"
                f"**Case ID:** {case}\n{f'**Reason:** {reason}' if reason else None}",
                color=ctx.author.color,
                timestamp=datetime.datetime.utcnow()
            )
            await c.send(embed=e, file=discord.File(f'./data/tickets/logs/{c_type}-{case}.txt'))
            if user is not None:
                try:
                    if c_type == 'idea':
                        c_type = 'dev '
                    await user.send(f"Hello {user.name}! thanks for contacting DragDev Studios {c_type}team:tm:. ~~if"
                                    f" you were happy with your service, please run `y!review {ctx.author.mention}"
                                    f" [rating of 1-10] [reason]`.~~ <- WIP, doesnt work\n i have included a copy of your ticket's transcript."
                                    f" have a great day/night <3", file=discord.File(
                        f'./data/tickets/logs/bug-{case}.txt'))
                except discord.Forbidden:
                    pass
        else:
            await ctx.send("Invalid ticket.")
    @commands.command()
    @checks.support_guild()
    async def support_case(self, ctx, case_id: str):
        """Get a case ID"""
        try:
            await ctx.send(file=discord.File(f'./data/tickets/logs/bug-{case_id}.txt'))
        except FileNotFoundError:
            try:
                await ctx.send(file=discord.File(f'./data/tickets/logs/support-{case_id}.txt'))
            except FileNotFoundError:
                files = "Valid file IDs:\n"
                for file in os.listdir('./data/tickets/logs'):
                    file = file.strip('.txt').strip('support-').strip('bug-')
                    files += f"{file}\n"
                await ctx.send(files)

    @commands.command(name='ticket', aliases=['support', 'new', 'sos'])
    @checks.support_guild()
    async def support(self, ctx, *, reason: str = None):
        """Open a support ticket

        you may include a reason"""
        inu = await ctx.send("Checking for open reports...")
        if str(ctx.author.id) in os.listdir('./data/tickets/support'):
            await inu.edit(content="ticket already open; finding...")
            for x in ctx.guild.text_channels:
                if x.name.startswith('support-') and x.name.endswith(str(ctx.author.id)):
                    return await inu.edit(content=f"Please go to {x.mention} first ^_^")
        else:
            await inu.edit(content="Creating ticket")
            fi = open(f'./data/tickets/support/{str(ctx.author.id)}', 'w+')
            fi.write(str(ctx.author.id))
            fi.close()
            for x in ctx.guild.categories:
                if x.name == 'tickets':
                    cat = x
                    support_role = discord.utils.get(ctx.guild.roles, name='Support')
                    dev = discord.utils.get(ctx.guild.roles, name='Developer')
                    overwrites = {
                        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                        ctx.guild.me: discord.PermissionOverwrite(read_messages=True),
                        ctx.author: discord.PermissionOverwrite(read_messages=True, send_messages=True,
                                                                embed_links=True,
                                                                attach_files=True),
                        support_role: discord.PermissionOverwrite(read_messages=True, send_messages=True,
                                                                  embed_links=True,
                                                                  attach_files=True)

                    }
                    chan = await cat.create_text_channel(f'support-{str(ctx.author.id)}', overwrites=overwrites,
                                                         reason=f"Ticket created by {ctx.author}",
                                                         topic=str(ctx.author.id))
                    await chan.send(f"Our {support_role.mention}s have been notified about your issue\n" 
                                    "if you havent already, check out our status page @ https://ylb.statuspal.io/?lang=en\nINFO:\n"
                                    f"{None if reason is None else escape(reason, mass_mentions=True, formatting=False, invites = False)}")
                    return await inu.edit(content=f"Please go to {chan.mention} ^_^")

    @commands.command(aliases=['feature', 'request'])
    @checks.support_guild()
    async def idea(self, ctx, *, idea: str = None):
        """Open a ticket to suggest something

        pings devs | takes a `reason` param"""
        inu = await ctx.send("Checking for open reports...")
        if str(ctx.author.id) in os.listdir('./data/tickets/ideas'):
            await inu.edit(content="ticket already open; finding...")
            for x in ctx.guild.text_channels:
                if x.name.startswith('idea-') and x.name.endswith(str(ctx.author.id)):
                    return await inu.edit(content=f"Please go to {x.mention} first ^_^")
        else:
            await inu.edit(content="Creating ticket")
            fi = open(f'./data/tickets/ideas/{str(ctx.author.id)}', 'w+')
            fi.write(str(ctx.author.id))
            fi.close()
            for x in ctx.guild.categories:
                if x.name == 'tickets':
                    cat = x
                    support_role = discord.utils.get(ctx.guild.roles, name='Support')
                    dev = discord.utils.get(ctx.guild.roles, name='Developer')
                    overwrites = {
                        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                        ctx.guild.me: discord.PermissionOverwrite(read_messages=True),
                        ctx.author: discord.PermissionOverwrite(read_messages=True, send_messages=True,
                                                                embed_links=True,
                                                                attach_files=True),
                        support_role: discord.PermissionOverwrite(read_messages=True, send_messages=True,
                                                                  embed_links=True,
                                                                  attach_files=True)

                    }
                    chan = await cat.create_text_channel(f'idea-{str(ctx.author.id)}', overwrites=overwrites,
                                                         reason=f"Ticket created by {ctx.author}",
                                                         topic=str(ctx.author.id))
                    await chan.send(f"Our {dev.mention}s have been notified about your suggestion\nINFO:\n"
                                    f"{None if idea is None else escape(idea, mass_mentions=True, formatting=False, invites = False)}")
                    return await inu.edit(content=f"Please go to {chan.mention} ^_^")

    @commands.command()
    @commands.has_any_role("Support", "Developer")
    @checks.support_guild()
    async def ticket_info(self, ctx, channel: discord.TextChannel = None):
        if channel is None:
            channel = ctx.channel
        channel_author = int(channel.topic)
        user = discord.utils.get(ctx.guild.members, id=channel_author)
        e = discord.Embed(
            title=channel.name,
            description=f"Author: {user.mention}\nCreated {Humanreadable.dynamic_time(channel.created_at)}\n"
            f"type: {channel.name.strip(str(user.id)).strip('-')}",
            color=user.color
        )
        await ctx.send(embed=e)
    
    async def sotw(self, ctx):
        from random import choice, randint
        server = choice(self.bot.guilds)
        # construct the embed
        if server.me.guild_permissions.manage_guild:
            invites = await server.invites()
            for i in invites:
                if i.max_age == 0 and i.max_uses == 0:
                    invite = i.url
                    break
        else:
            invite = None
        icon = server.icon_url
        bots = 0
        humans = 0
        total = len(server.members)
        for x in server.members:
            if x.bot:
                bots += 1
            else:
                humans += 1
        owner = server.owner.name
        from utils.formatting import Humanreadable
        created = Humanreadable.dynamic_time(server.created_at)
        since = Humanreadable.dynamic_time(server.me.joined_at)
        co = server.owner.color
        e = discord.Embed(title="Server of the week:", description = f"Name: **{server.name}**\nCreated **{created}**\ni joined **{since}**\nChannels: **{len(server.channels)}**\nMembers: **{humans}**\nBots: **{bots}**\nOwner: **{owner}**\n**invite:** {invite}", color=co)
        e.set_thumbnail(url=icon)
        c = discord.utils.get(ctx.guild.text_channels, name="server-of-the-day")
        await c.send(f"GG {server.owner.mention}! You won server of the week!", embed=e)

    @commands.command(aliases=['reserve'])
    @checks.support_guild()
    @commands.has_any_role("Support", "Developer")
    async def preserve(self, ctx, backup_user_optional: discord.User = None):
        """Preserve a ticket with a message telling not to close"""
        await ctx.message.delete(delay=1)
        try:
            user = int(ctx.channel.name.strip('idea-').strip('support-').strip('bug-'))
            member = discord.utils.get(ctx.guild.members, id=user)
            if member is None:
                await ctx.send('Unable to find a member with the ID {}. I will still leave a message.', delete_after=5)
                await asyncio.sleep(5)
            e = discord.Embed(
    name='**Ticket Reservation**', description='This ticket has been preserved from being closed by {0} for {1}. Do not close.'.format(ctx.author.mention, '*unknown*' if member is None else member.mention),
    color = member.color if member is not None else ctx.author.color, 
    timestamp=datetime.datetime.utcfromtimestamp(_time.time() + 86400)
)
            e.set_footer(text='can be closed in:')
            await ctx.send(embed=e)
            await ctx.message.delete()
        except:
            raise
    @commands.command(aliases=['remind, alert'])
    @checks.support_guild()
    @commands.has_any_role('Support', 'Developer')
    async def prompt(self, ctx):
        """remind someone if they have left a ticket."""
        await ctx.message.delete(delay=1)
        try:
            user = int(ctx.channel.name.strip('idea-').strip('support-').strip('bug-'))
            member = discord.utils.get(ctx.guild.members, id=user)
            if member is None:
                return await ctx.send(f'Unable to find a member with the ID {member}. I will still leave a member with the ID {member}. Closing is advised.')
            e = discord.Embed(title="don’t forget about me!", description=f"{member.mention} you left this channel alone! if I don’t receive a reply within 12h you run the risk of the ticket being closed!",
            color=random.choice([ctx.author.color, member.color]), timestamp=datetime.datetime.utcnow())
            e.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
            await ctx.message.delete()
            for I in range(3):
                await ctx.send(member.mention, delete_after=0.01)
            msg = await ctx.send(embed=e)
            await ctx.message.delete()
            def c(m):
                return m.channel == ctx.channel
            try:
                await self.bot.wait_for('message', check=c, timeout=43200)
                await msg.delete()
            except asyncio.TimeoutError:
                e.set_footer(text='it has been 12h. Staff are clear to close.')
                await msg.edit(content=None, embed=e)
        except:
            await ctx.send('invalid ticket')

    @commands.command(aliases=["timedclose", "tc", "ac", "auto"])
    @checks.support_guild()
    @commands.has_any_role('Support', 'Developer')
    async def autoclose(self, ctx, time = '12h'):
        """Set a ticket to autoclose. Include s, h, m or d"""
        timo = time
        d = 86400
        h = 3600
        m = 60
        s = 1  # multiplying by 0 isn’t possible for s
        time = time.lower()
        if time.endswith('d'):
            time = time.strip('d')
            time = float(time) * d
        elif time.endswith('h'):
            time = time.strip('h')
            time = float(time) * h
        elif time.endswith('m'):
            time = time.strip('m')
            time = float(time) * m
        elif time.endswith('s'):
            time = time.strip('s')
            time = float(time) * s
        else:
            return await ctx.send('invalid ending; please provide a time in d, h, m, or s. Like `6m` would close in 6 minutes')
        e = discord.Embed(
        title=f"closing in {timo}",
        description="unless a message is sent my the ticket author or a support member says `cancel`.",
        timestamp=datetime.datetime.utcfromtimestamp(_time.time() + time),
        color=ctx.author.color)
        e.set_footer(text="Closing: ")
        e.set_author(icon_url=ctx.author.avatar_url, name=ctx.author.name)
        b = await ctx.send(embed=e)
        N = ctx.channel.name.strip('bug-').strip('idea-').strip('support-')
        author = discord.utils.get(self.bot.users, id=int(N))
        await ctx.message.delete()
        def c(m):
            return m.author == author or m.author == ctx.author and "cancel" in m.content.lower()
        try:
            d= await self.bot.wait_for('message', timeout=time, check=c)
            ca = discord.Embed(title=f"autoclose cancelled by {d.author.name}", color=discord.Color.green())
            ca.set_author(name=d.author.name)
            await b.edit(embed=ca)
        except asyncio.TimeoutError:
            await self.closemethod(ctx)

def setup(bot):
    bot.add_cog(TicketSystem(bot))
