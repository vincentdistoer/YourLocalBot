import asyncio
import datetime
import os
import random
import re
import time
import traceback
import typing
import unicodedata
from random import randint
from typing import Union
import json

import aiohttp
import discord
from discord.ext import commands

from utils import checks
from utils.escapes import *
from utils.formatting import Humanreadable as hr
from utils.page import pagify


# k 'k'
class GuildConverter(commands.Converter):
	async def guild(self, ctx, guild):
		try:
			for x in ctx.bot.guilds:
				if x.name == guild or str(x.id) == guild or x.owner == guild:
					return x.convert(ctx, guild)
			else:
				raise discord.NotFound('No guild with the name/id/owner {} found'.format(guild))
		except Exception as E:
			raise E


class MainCog(commands.Cog):

	def __init__(self, bot):
		self.bot = bot
		self.youtube_regex = (
			r'(https?://)?(www\.)?'
			'(youtube|youtu|youtube-nocookie)\.(com|be)/'
			'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})')
		self.cooldowns = []
		self.announcing = []
		self.dtf = "%I:%M %p @ %d/%m/%Y %Z"
		self.recieved = 0
		self.commanded = 0
		self.pings = {'delay': [], 'hb': []}
	@commands.Cog.listener()
	async def on_command(self, ctx):
		self.commanded += 1
	@commands.Cog.listener()
	async def on_message(self, m):
		self.recieved += 1

	@staticmethod
	def escape(text, *, mass_mentions=False, formatting=False, invites=False):
		if mass_mentions:
			text = text.replace("@everyone", "@\u200beveryone")
			text = text.replace("@here", "@\u200bhere")
		if formatting:
			text = (text.replace("`", "\\`")
					.replace("*", "\\*")
					.replace("_", "\\_")
					.replace("~", "\\~"))
		if invites:
			text = text.replace('ord.gg', 'ord\u200b.gg')
		return text

	def escape_mass_mentions(self, text, invites: bool=True):
		return self.escape(text, mass_mentions=True, invites=invites)

	def pagify(self, text, delims=["\n"], *, escape=True, shorten_by=8,
			   page_length=2000):
		"""DOES NOT RESPECT MARKDOWN BOXES OR INLINE CODE"""
		in_text = text
		if escape:
			num_mentions = text.count("@here") + text.count("@everyone")
			shorten_by += num_mentions
		page_length -= shorten_by
		while len(in_text) > page_length:
			closest_delim = max([in_text.rfind(d, 0, page_length)
								 for d in delims])
			closest_delim = closest_delim if closest_delim != -1 else page_length
			if escape:
				to_send = self.escape_mass_mentions(in_text[:closest_delim])
			else:
				to_send = in_text[:closest_delim]
			yield to_send
			in_text = in_text[closest_delim:]

		if escape:
			yield self.escape_mass_mentions(in_text)
		else:
			yield in_text

	@commands.command()
	@commands.is_owner()
	async def kill(self, ctx):
		"""quit the bot
		"""
		await self.bot.close()
	@commands.command()
	async def ball(self, ctx, text):
		c = ['yes', 'no', 'idk', 'certainly','certainly not']
		await ctx.send(random.choice(c))
	@commands.command()
	@commands.bot_has_permissions(manage_roles=True, manage_guild=True)
	async def roleinfo(self, ctx, role: discord.Role):
		def check(m):
			return (m.channel, m.author) == (ctx.channel, ctx.author)
		message = await ctx.send('gathering info...')
		name = role.name
		id = role.id
		created_at = hr.dynamic_time(role.created_at)
		members = role.members
		mentionable = role.mentionable
		hoister_no_hoisting = role.hoist
		hex = role.color
		e = discord.Embed(
			title=role.name + '\'s info:',
			description=f"**Name:** `{name}`\n**ID:** `{id}`\n**Created:** {created_at}\n**Members:** {len(members)}\n**Hex color:** {hex}\n**Hoisted:** {hoister_no_hoisting}\n**Mentionable:** {mentionable}",
			timestamp=role.created_at,
			color=hex
		)
		return await message.edit(content=None, embed=e)

	@commands.command()
	async def invite(self, ctx, bot: discord.User = None):
		"""Invite me/@bot!"""
		if bot:
			if bot.bot:
				bot = bot.id
			else:
				bot = 0
			url = discord.utils.oauth_url(bot)
		else:
			bot = self.bot.user.id
			url = "<https://discordapp.com/api/oauth2/authorize?client_id=558689453573406771&permissions=152431681&redirect_uri=https%3A%2F%2Finvite.gg%2Febot&scope=bot>"
		if bot in [517008210905923594, 553622350952923146, 558689453573406771]:
			ss = '<https://invite.gg/ebot>'
		elif bot in [541646089347137537, 481810078031282176]:
			ss = '<https://invite.gg/db>'
		elif bot in [554852324376313856, 554091196235120651]:
			ss = '<https://invite.gg/jadbots>'
		else:
			ss = None
		ft = f"Invite URL: **{url}**"
		if ss is not None:
			ft += f"\nSupport Guild: **{ss}**"
		await ctx.send(f"{ft}")

	@commands.command()
	@checks.co_owner()
	async def reboot(self, ctx):
		"""Reboot the bot"""
		try:
			await self.bot.change_presence(activity=None, status=discord.Status.offline)
			exit(1)
		except:
			print("Rebooting...")
			exit(1)
		finally:
			if self.bot.user.name.lower().endswith('dev'):
				os.system('python devbot.py')
			else:
				os.system('python3.7 makeitwork.py')

	@commands.command()
	@commands.bot_has_permissions(administrator=True)
	@commands.guild_only()
	async def announce(self, ctx):
		"""Announce a message"""
		tomention = []
		admin = ctx.message.author.guild_permissions.administrator
		mention = ctx.message.author.guild_permissions.mention_everyone
		if ctx.author.id in self.announcing:
			return await ctx.send("you are currently in an announce session! to get a new one, say `exit`.")
		else:
			self.announcing.append(ctx.author.id)
		url = None
		thumbnail = False
		image = False
		e = discord.Embed(title="Arguments", description=f"Hello {ctx.author.mention}! please say any of the follow"
		f"ing arguments:", color=ctx.author.color)
		e.add_field(name="everyone", value="Adds an @everyone to your announcement; requires mention_everyone")
		e.add_field(name="here", value="Adds an @here to your announcement; requires mention_everyone")
		e.add_field(name="rolemention", value="Adds @role to your announcement")
		e.add_field(name="url", value="Sets the url for the title; can be used by anyone")
		e.add_field(name="thumbnail", value="sets the little icon in the top right of the embed. discordapp links"
											" are the only accepted links.")
		e.add_field(name="image", value="sets the large image of the embed, discordapp links only.")
		e.add_field(name="finish", value="finish creating the embed and move on to setting it's contents.")
		e.add_field(name="exit", value='quits the creation and deletes all stored data.')
		ce = discord.Embed(title="Checking...", color=discord.Color.blurple())
		np = discord.Embed(title="You lack permissions!", color=discord.Color.red())
		msg = await ctx.send(embed=e)
		while True:
			await msg.edit(embed=e)

			def check(m):
				return m.author == ctx.author and m.channel == ctx.channel

			x = await self.bot.wait_for('message', check=check)
			await x.delete()
			# lets get to work
			# first, lets go in the above order
			# ====
			# EVERYONE_MENTION:
			if x.content in ['ev', 'everyone', 'Everyone']:
				await msg.edit(embed=ce)
				if ctx.author == ctx.guild.owner:
					pass
				else:
					if not admin or not mention:
						await msg.edit(embed=np)
						await asyncio.sleep(5)
					else:
						pass
				tomention.append('@everyone')
				await msg.edit(embed=e)
			# HERE:
			elif x.content in ['he', 'here', 'Here']:
				await msg.edit(embed=ce)
				if ctx.author == ctx.guild.owner:
					pass
				else:
					if not admin or not mention:
						await msg.edit(embed=np)
						await asyncio.sleep(5)
					else:
						pass
				tomention.append('@here')
				await msg.edit(embed=e)
			# ROLEMENTION
			elif x.content in ['rm', 'role', 'rolemention', 'Rolemention']:
				fin = False
				await msg.edit(embed=None, content="Please give me a role name/id. names are case sensitive")
				while fin is False:
					r = await self.bot.wait_for('message', check=check)
					await r.delete()
					await msg.edit(embed=ce)
					for x in ctx.guild.roles:
						if x.name == r.content:
							tomention.append(x.mention)
							fin = True
							break
						elif str(x.id) == r.content:
							tomention.append(x.mention)
							fin = True
							break
					else:
						await msg.edit(content="Role not found; try again.")
				await msg.edit(content="_ _", embed=e)

			# URL:
			elif x.content in ['u', 'url', 'Url']:
				await msg.edit(content="Gimme a link. any link.", embed=None)
				x = await self.bot.wait_for('message', check=check)
				if not x.content.startswith('https://') or not x.content.startswith("http://"):
					pass
				else:
					url = x.content
				await x.delete()

			# THUMBNAIL:
			elif x.content in ['th', 'thumb', 'Thumbnail', 'thumbnail']:
				await msg.edit(content="Gimme a link; preferably an image, so i can actually display it.\n"
									   "you can also mention someone to get their avatar instead", embed=None)
				x = await self.bot.wait_for('message', check=check)
				if x.content.startswith('@'):
					for m in ctx.guild.members:
						if m.mention == x:
							thumbnail = m.avatar_url
							break
				else:
					thumbnail = x.content
				await x.delete()
			# IMAGE:
			elif x.content in ['im', 'image', 'Image']:
				await msg.edit(content="Gimme a link; preferably an image, so i can actually display it.\n"
									   "you can also mention someone to get their avatar instead", embed=None)
				x = await self.bot.wait_for('message', check=check)
				if x.content.startswith('@'):
					for m in ctx.guild.members:
						if m.mention == x:
							image = m.avatar_url
							break
				else:
					image = x.content
				await x.delete()

			# poll
			elif x.content == 'poll':
				pass
			elif x.content == 'exit':
				self.announcing.remove(ctx.author.id)
				return await ctx.send("ok, bye!")
			elif x.content == 'finish':
				break
			else:
				pass
		await msg.edit(content="please tell me a title...", embed=None)  # embed=None clears the embed
		x = await self.bot.wait_for('message', check=check)
		title = x.content
		await x.delete()
		await msg.edit(content="and a description...")
		x = await self.bot.wait_for('message', check=check)
		description = x.content
		await x.delete()
		await msg.edit(content="and a footer (say `None` to leave blank`)")
		x = await self.bot.wait_for('message', check=check)
		if x.content == 'None':
			footer = ctx.author.name
		else:
			footer = x.content
		await x.delete()
		await msg.edit(content="and finally, a color\nValid colors: `red`/`orange`/`yellow`/`green`/`blue`/"
							   "`purple`/`blurple`. say `default` to default to your name color")
		while True:
			x = await self.bot.wait_for('message', check=check)
			await x.delete()
			x = x.content.lower()
			if x == 'default':
				color = ctx.author.color
				break
			elif x == 'red':
				color = discord.Color.red()
				break
			elif x == 'orange':
				color = discord.Color.orange()
				break
			elif x == 'yellow':
				color = discord.Color.gold()
				break
			elif x == 'green':
				color = discord.Color.green()
				break
			elif x == 'blue':
				color = discord.Color.blue()
				break
			elif x == 'purple':
				color = discord.Color.purple()
				break
			elif x == 'blurple':
				color = discord.Color.blurple()
				break
			else:
				pass

		mentions = ' | '.join(tomention)
		try:
			e = discord.Embed(title=title, description=description, color=color, timestamp=datetime.datetime.utcnow())
			if url:
				e.url = url
			if thumbnail != False:
				try:
					e.set_thumbnail(url=thumbnail)
				except:
					pass
			if image != False:
				try:
					e.set_image(url=image)
				except:
					pass
			e.set_footer(text=footer)
			e.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			while True:
				await msg.edit(content="Please mention a channel, give it's id or name.", embed=None)
				ccc = await self.bot.wait_for('message', check=check)
				c = ccc.content
				await ccc.delete()
				for x in ctx.guild.channels:
					if x.name == c.lower() or str(x.id) == c or x.mention == c:
						if len(tomention) == 0:
							content = None
						else:
							content = mentions
						await x.send(content=content, embed=e)
						await msg.edit(content=f"Successfully sent to {x.mention}")
						self.announcing.remove(ctx.author.id)
						return await ctx.message.delete()
				else:
					await ctx.send("channel not found. try again.")
		except Exception as e:
			await msg.edit("Unexpected error; quitting")
			self.announcing.remove(ctx.author.id)
			raise e

	@commands.group(aliases=['user', 'memberinfo'], invoke_without_command=True)
	@commands.guild_only()
	@commands.bot_has_permissions(embed_links=True)
	async def userinfo(self, ctx, member: typing.Union[discord.Member, discord.User, int]=None):
		"""Get member's info"""
		if ctx.invoked_subcommand is not None:
			return
		if member is None:
			member = ctx.author
		if isinstance(member, discord.Member) or member is None:
			joined = member.joined_at.strftime(self.dtf)
			disp = member.display_name
			status = str(member.status)
			on_mobile = member.is_on_mobile()
			roles = {
				"top": member.top_role,
				"total": len(member.roles)
			}
			av = member.avatar_url_as(static_format='png')
			bot = member.bot
			created = member.created_at.strftime(self.dtf)
			e = discord.Embed(
				title=f"{member.name}'s information:",
				description=f"**Joined:** {joined}\n**Created:** {created}\n**Display Name:** {disp}\n**Status:** "
				f"{status}\n**Using Mobile:** {on_mobile}\n**roles:**\n-> top: {roles['top']}\n-> total: "
				f"{roles['total']}\n**Avatar URL:** {av}\n**Bot:** {bot}",
				color=member.color
			)
			e.set_thumbnail(url=str(av))
			return await ctx.send(embed=e)
		elif isinstance(member, discord.User):
			joined = 'N/A'
			disp = member.name
			status = 'N/a'
			on_mobile = 'N/A'
			roles = {
				"top": 'N/A',
				"total": 0
			}
			av = member.avatar_url_as(static_format='png')
			bot = member.bot
			created = member.created_at.strftime(self.dtf)
			e = discord.Embed(
				title=f"{member.name}'s information:",
				description=f"**Joined:** {joined}\n**Created:** {created}\n**Display Name:** {disp}\n**Status:** "
				f"{status}\n**Using Mobile:** {on_mobile}\n**roles:**\n-> top: {roles['top']}\n-> total: "
				f"{roles['total']}\n**Avatar URL:** {av}\n**Bot:** {bot}",
				color=discord.Color.blurple()
			)
			e.set_thumbnail(url=str(av))
			return await ctx.send(embed=e)
		else:  # int
			try:
				member = await self.bot.fetch_user(member)
			except:
				return await ctx.send(f"User with the id {member} does not exist!")
			joined = 'N/A'
			disp = member.name
			status = 'N/a'
			on_mobile = 'N/A'
			roles = {
				"top": 'N/A',
				"total": 0
			}
			av = member.avatar_url_as(static_format='png')
			bot = member.bot
			created = member.created_at.strftime(self.dtf)
			e = discord.Embed(
				title=f"{member.name}'s information:",
				description=f"**Joined:** {joined}\n**Created:** {created}\n**Display Name:** {disp}\n**Status:** "
				f"{status}\n**Using Mobile:** {on_mobile}\n**roles:**\n-> top: {roles['top']}\n-> total: "
				f"{roles['total']}\n**Avatar URL:** {av}\n**Bot:** {bot}",
				color=discord.Color.blurple()
			)
			e.set_thumbnail(url=str(av))
			return await ctx.send(embed=e)

	@userinfo.command()
	@commands.guild_only()
	async def roles(self, ctx, user: discord.Member = None):
		"""get users roles"""
		user = ctx.author if user is None else user
		rn = ""
		for x in reversed(user.roles):
			rn += f"• `{x.name}`\n"
		e=discord.Embed(title=user.name + "'s roles:", description=rn, color=user.color)
		e.set_footer(text=f"Top role: {user.top_role.name}")
		await ctx.send(embed=e)

	@commands.command(name='perms', aliases=['perms_for', 'permissions'])
	@commands.guild_only()
	async def check_permissions(self, ctx, *, thing: Union[discord.Member, discord.Role] = None):
		"""A simple command which checks a member's or role's Guild Permissions.
		If member is not provided, the author will be checked."""
		if not thing:
			thing = ctx.author
		if isinstance(thing, discord.Role):
			resolved_ = []
			role = thing
			raw_perms = dict(thing.permissions)
			for value in list(dict(thing.permissions)):
				if raw_perms[value] is True:
					resolved_.append(str(value).replace('_', ' '))
			if len(resolved_) == 0:
				resolved_.append("How strange. This role has no permissions!")
			e=discord.Embed(title="Permissions:", description='\n• '.join(resolved_), color=role.color)
			return await ctx.send(embed=e)

		# Here we check if the value of each permission is True.
		member = thing
		perms = '\n'.join(perm for perm, value in member.guild_permissions if value)
		if 'administrator' in perms:
			perms = 'administrator (all perms)'

		# And to make it look nice, we wrap it in an Embed.
		embed = discord.Embed(title='Permissions for:', description=perms, colour=member.colour)
		embed.set_author(name=member.name, icon_url=member.avatar_url)
		await ctx.send(content=None, embed=embed)

	@commands.command()
	@commands.bot_has_permissions(embed_links=True)
	async def av(self, ctx, *, user: typing.Union[discord.Member, discord.User]=None, _format: str = 'png', size: int = 1024):
		"""get someones avatar"""
		if user is None:
			user = ctx.author

		av = user.avatar_url_as(static_format=_format, size=size)
		_type = 'png'
		if user.is_avatar_animated():
			_type = 'gif'
		e = discord.Embed(description=f"url: **<{av}>**\nType: **{_type}**\nsize: {size}x{size}\nPreview:")
		e.set_image(url=str(av))
		return await ctx.send(embed=e)

	@commands.command()
	@checks.gowner()
	@commands.guild_only()
	@commands.bot_has_permissions(administrator=True)
	async def killswitch(self, ctx, saved_channels: commands.Greedy[discord.TextChannel]=None):
		"""delete all chennels"""
		m = await ctx.send('<a:loading20:553253741311295498>')
		tod = []
		# log = {"channels": [], "roles": []}
		saved_channels = [] if saved_channels is None or len(saved_channels) == 0 else saved_channels
		for x in ctx.guild.channels:
			if x not in saved_channels:
				tod.append(x)
		for x in ctx.guild.roles:
			if not x >= ctx.guild.me.top_role:
				tod.append(x)
		code = random.randint(111111, 999999)
		await m.edit(content=f'Hello {ctx.author.name}! `killswitch` is a utility that is designed for resetting servers '
		f'quickly and efficiently. Disclaimer: ```YLB (yourlocalbot), its users and global associates (known as developer, '
		f'global Admins and global Mods) take no responsibility for any damages this command will cause, and you (the user) agree '
		f'with this by typing the security code below, hereby giving your consent and agreeing that all damages are on your behalf```'
		f'Security code: ||{code}||')
		def check(m):
			return m.author == ctx.author and m.channel == ctx.channel and m.content == str(code)
		try:
			B = await self.bot.wait_for('message', check=check, timeout=30)
		except asyncio.TimeoutError:
			return await ctx.send('cancelled')
		await m.edit(content="consent given. Executing...")
		for x in tod:
			try:
				await x.delete(reason="killswitch")
			except:
				pass
		done = await ctx.guild.create_text_channel('done')
		await done.send("@everyone killswitch complete.")

	@commands.command()
	@checks.gowner()
	async def makeaguild(self, ctx):
		"""Interactive server setup tour"""
		pass


	@commands.command(aliases=['leetify', 'leet'])
	async def l33tify(self, ctx, *, text: str = 'idiot forgot to supply text to change!'):
		"""l33tify text.

		source: http://www.robertecker.com/hp/research/leet-converter.php?lang=en"""
		c = text
		c = c.replace('a', '3').replace('e', '3').replace('g', '6').replace('i', '1')
		c = c.replace('o', '0').replace('s', '5').replace('j', '7')
		c = c.replace('A', '3').replace('E', '3').replace('G', '6').replace('I', '1')
		c = c.replace('O', '0').replace('S', '5').replace('J', '7')
		await ctx.send(f"Output: `{c}`.")

	@commands.command()
	async def pi(self, ctx, amount: int = 314):
		"""get pi."""
		if amount >= 2000:
			amount = 1998
		pi = '3.1415926535897932384626433832795028841971693993751058209749445923078164062862089986280348253421170' \
			 '679821480865132823066470938446095505822317253594081284811174502841027019385211055596446229489549303' \
			 '819644288109756659334461284756482337867831652712019091456485669234603486104543266482133936072602491' \
			 '412737245870066063155881748815209209628292540917153643678925903600113305305488204665213841469519415' \
			 '116094330572703657595919530921861173819326117931051185480744623799627495673518857527248912279381830' \
			 '119491298336733624406566430860213949463952247371907021798609437027705392171762931767523846748184676' \
			 '694051320005681271452635608277857713427577896091736371787214684409012249534301465495853710507922796' \
			 '892589235420199561121290219608640344181598136297747713099605187072113499999983729780499510597317328' \
			 '160963185950244594553469083026425223082533446850352619311881710100031378387528865875332083814206171' \
			 '776691473035982534904287554687311595628638823537875937519577818577805321712268066130019278766111959' \
			 '092164201989380952572010654858632788659361533818279682303019520353018529689957736225994138912497217' \
			 '752834791315155748572424541506959508295331168617278558890750983817546374649393192550604009277016711'
		await ctx.send(pi[0:(amount + 1)])

	@commands.command(pass_context=True, name='youtube', no_pm=True)
	@commands.guild_only()
	async def _youtube(self, ctx, *, query: str):
		"""Search on Youtube. channel must be flagged NSFW"""
		if not ctx.channel.is_nsfw():
			return await ctx.send("Channel must be NSFW. sorry.")
		try:
			url = 'https://www.youtube.com/results?'
			payload = {'search_query': ''.join(query)}
			headers = {'user-agent': 'Red-cog/1.0'}
			conn = aiohttp.TCPConnector()
			session = aiohttp.ClientSession(connector=conn)
			async with session.get(url, params=payload, headers=headers) as r:
				result = await r.text()
			await session.close()
			yt_find = re.findall(r'href=\"/watch\?v=(.{11})', result)
			url = ' Your top result:\nhttps://www.youtube.com/watch?v={}'.format(yt_find[0])
			await ctx.send(url)
		except Exception as e:
			message = 'Something went terribly wrong! [{}]'.format(e)
			await self.bot.say(message)

	@commands.command(alias=['pang', 'pong'])
	@commands.bot_has_permissions(embed_links=True)
	async def ping(self, ctx):
		"""Get the bots ping"""
		heartbeat = f'{ctx.bot.latency * 1000:.0f}'
		start_delay = time.time()
		delay = await ctx.send("Pinging...")
		end_delay = round((time.time() - start_delay) * 1000)
		with open("./data/eco.json", 'r') as file:
			f_start = time.time()
			json.load(file)
			file.close()
			f_end = round((time.time() - f_start) * 1000, 2)
		color = discord.Color.blurple()
		e = discord.Embed(title="Pong!", description=f"**Heartbeat**: {heartbeat}ms\n**Delay**: {end_delay}ms\n"
		f"**Database**: {f_end}ms", color=color, timestamp=datetime.datetime.utcnow())
		av = 0
		for c in self.pings['delay']:
			av += c
		try:
			e.set_footer(text='Average ping: ' + str(round((av / len(self.pings['delay'])), 2)) + "ms")
		except:
			pass
		await delay.edit(content=None, embed=e)
		self.pings['delay'].append(end_delay)
		self.pings['hb'].append(heartbeat)

	@commands.group(invoke_without_command=True)
	@commands.guild_only()
	@commands.bot_has_permissions(embed_links=True)
	async def serverinfo(self, ctx, guild: int = None):
		"""get a servers info!

		specify a guild's id and, if im in it, i will display it's info too!"""
		roles = 0
		members = 0
		bots = 0
		initial = await ctx.send("Finding guild...")
		if guild is None:
			guild = ctx.guild
		else:
			guild = self.bot.get_guild(guild)
			if guild is not None:
				guild = guild
			else:
				return await ctx.send("guild not found. run `servers` to get a list of guilds.")
		await initial.edit(content=f"Gathering {guild.name}'s information...")

		try:
			# role
			check = 0
			top_three = ""
			for r in reversed(guild.roles):
				check += 1
				if check > 3:
					pass
				else:
					if check == 2:
						top_three += f"• **{r.name}**\n"
					else:
						top_three += f"• **{r.name}**\n"
				roles += 1
			# members, bots, total
			for m in guild.members:
				if m.bot:
					bots += 1
				else:
					members += 1
			total = bots + members
			owner = f"{guild.owner} ({guild.owner.id})"
			try:
				urls = []
				invites = await guild.invites()
				for x in invites:
					urls.append(x.url)
				url = random.choice(urls)
			except (discord.Forbidden, discord.HTTPException):
				url = 'http://discord.gg/d3zRBsc'
			e = discord.Embed(title=f"{guild.name}'s information!", color=guild.owner.color,
							  timestamp=datetime.datetime.utcnow())
			e.url = url
			e.add_field(name='User information:', value=f"Total members: {guild.member_count}\nHumans: "
			f"{members}\nBots: {bots}\nOwner:"
			f" {owner}")
			e.add_field(name="Role information:", value=f"Total roles: {roles}\nTop 3 roles:\n{top_three}")
			try:
				tbans = 0
				bans = await guild.bans()
				for b in bans:
					tbans += 1
				e.add_field(name="Bans:", value=str(tbans), inline=False)

			except (discord.Forbidden, discord.HTTPException):
				pass
			if guild.default_notifications == discord.NotificationLevel.only_mentions:
				nl = 'Only Mentions'
			elif guild.default_notifications == discord.NotificationLevel.all_messages:
				nl = 'All Messages'
			else:
				nl = 'unknown'  # this should NEVER happen

			e.add_field(name="Category info:", value=f"total categories: {len(guild.categories)}\ntotal channels: "
			f"{len(guild.text_channels) + len(guild.voice_channels)}\n of which text: {len(guild.text_channels)}\n"
			f"of which voice: {len(guild.voice_channels)}")
			e.add_field(name="Verification level:", value=str(guild.verification_level))
			e.add_field(name="Content filter level:", value=guild.explicit_content_filter)
			e.add_field(name="Notification settings:", value=nl)
			if guild.max_members is None:
				max_members = "5000"
			else:
				max_members = guild.max_members
			e.add_field(name="Max members:", value=f"{guild.member_count}/{max_members}")
			e.add_field(name="Other:", value=f"Total emojis: {len(guild.emojis)}\nRegion: "
			f"{str(guild.region).replace('-', ' ')}\n"
			f"Afk Timeout: {guild.afk_timeout}\nID: {guild.id}")
			e.set_thumbnail(url=guild.icon_url)
			await initial.edit(content=None, embed=e)
		except Exception as e:
			await initial.edit(content=f"Error\n`{e}`")
			raise e

	@serverinfo.command(name="roles")
	async def _roles(self, ctx):
		"""List server roles"""
		out = []
		for rank, role in enumerate(reversed(ctx.guild.roles), start=1):
			out.append(f'{rank}: `{role.name}` ({len(role.members)} member{"s" if len(role.members) != 1 else ""})')
			if role == ctx.author.top_role:
				user_rank = rank
		e = discord.Embed(description='\n'.join(out), color=ctx.author.color)
		e.set_footer(text=f'you are no. {user_rank} in the rank hierarchy.')
		await ctx.send(embed=e)

	@commands.group()
	@checks.co_owner()
	async def servers(self, ctx):
		"""list servers"""
		if ctx.invoked_subcommand is None:
			pages = commands.Paginator()
			for num, guild in enumerate(self.bot.guilds, start=1):
				pages.add_line(f"{num}. {guild.name} ({guild.id})")
				pages.add_line(empty=True)
			for page in pages.pages:
				await ctx.send(page)
				await asyncio.sleep(1)
			await ctx.send(f"Guilds: {len(self.bot.guilds)}\nPages: {len(pages.pages)}")

	@servers.command(name='invite')
	@checks.gcmod()
	async def invit(self, ctx, guild: typing.Union[int, discord.Guild]):
		"""invite to a guild."""
		f = await ctx.send("Searching through guilds...")
		if isinstance(guild, discord.Guild):
			guild = guild.id
		g = self.bot.get_guild(guild)
		if g is None:
			return await f.edit(content="guild not found")
		else:
			await f.edit(content="guild found!")
		totalinvs = []
		try:
			invs = await g.invites()
			for inv in invs:
				totalinvs.append(inv.url)
			invite = random.choice(totalinvs)
			await f.edit(content=invite)
		except:
			await f.edit(content="Unable to gain invites - attempting creation...")
			for c in g.text_channels:
				try:
					inv = await c.create_invite(max_age=84600, max_uses=1, reason='Developer '
																				  'used invite command to '
																				  'get an invite.')
					await f.edit(content=inv.url)
					break
				except:
					return await f.edit(content="Unable to get or create invite.")

	@servers.command()
	@checks.gcmod()
	async def msg(self, ctx, guild: int, anon: typing.Optional[bool], *, message: str):
		"""msg server owner"""
		a = discord.Permissions.administrator
		c = discord.Permissions.create_instant_invite
		f = await ctx.send("Looking for guild")
		g = self.bot.get_guild(guild)
		if g is None:
			return await f.edit(content="guild not found")
		else:
			await f.edit(content="Found guild! attempting to message...")
			e = discord.Embed(title="Message from my developer", description=message, color=g.me.color)
			if not anon:
				e.set_author(icon_url=ctx.author.avatar_url, name=ctx.author.name)
			try:
				await g.owner.send(embed=e)
				await f.edit(content="Success! preview:", embed=e)
			except discord.Forbidden:
				pi = g.me.guild_permissions
				if g.owner not in ctx.guild.members and a not in pi and c not in pi:
					ra = 'leave'
				elif g.owner in ctx.guild.members:
					ra = f'dm {g.owner.mention}'
				else:
					ra = 'try creating an invite'
				await f.edit(content=f"Unable to message owner; recommended action: {ra}")

	@servers.command()
	@checks.gcmod()
	async def leave(self, ctx, guild: int, *, reason: str = 'unspecified reason'):
		"""leave a guild via ID"""
		await ctx.send("finding server...")
		g = self.bot.get_guild(guild)
		if g is None:
			return await ctx.send("Unable to find guild")
		else:
			try:
				await g.owner.send(f"I have been ordered to leave your server ({g.name})"
								   f" by my developer, for the reason `"
								   f"{reason}`. bye!")
			except:
				try:
					await g.system_channel.send(f'I have been ordered to leave your server for: {reason}. You may add me back at a later date should you desire.')
				except:
					pass
			finally:
				await g.leave()
				await ctx.send("Success!")

	@servers.group(name='ban')
	@checks.gcadmin()
	async def _ban(self, ctx, guild_id: int, *, reason: str = 'No reason Provided.'):
		"""ban a guild from using the bot. """
		m = await ctx.send("Finding guild...")
		g = self.bot.get_guild(guild_id)
		if g is None:
			return await m.edit(content="thats not a guild, dumdum. if it is please run `...ban force <id>` instead.")
		await m.edit(content="banning guild and contacting owner...")
		try:
			await g.owner.send(f"Your guild (\"{g.name}\") has been banned from using me, for the reason below. i will "
							   f"now leave. bye!\n>>> {reason}")
		except:
			pass  # we dont care
		with open('./data/general.json', 'r') as fp:
			data = json.load(fp)
		data['banned']['guilds'][str(guild_id)] = [reason, ctx.author.id]
		with open('./data/general.json', 'w') as fp:
			json.dump(data, fp)
		return await m.edit(content="done.")


	@commands.command(aliases=['rmsg', 'randommessage', 'rmessage'])
	@commands.guild_only()
	@commands.bot_has_permissions(read_message_history=True, embed_links=True)
	@commands.cooldown(1, 65, commands.BucketType.user)
	async def randommsg(self, ctx, channel: discord.TextChannel = None):
		"""get a random message from [channel]!"""
		async with ctx.channel.typing():
			if channel is None:
				channel = ctx.channel
			msgobjs = []
			async for m in channel.history(limit=10000):
				msgobjs.append(m)
		m = random.choice(msgobjs)
		if len(m.embeds) < 1:
			e = discord.Embed(title=f"Message from {m.created_at.strftime(self.dtf)} by {m.author.name}:",
							  description=m.content, url=m.jump_url, color=m.author.color if m in m.guild.members else discord.Color.blurple(),
							  timestamp=m.created_at)
			await ctx.send(embed=e)
		else:
			new = f"Message from {m.author.name}<:bot:523195448085970947>:"
			await ctx.send(new, embed=m.embeds[0])

	@staticmethod
	def _dynamic_time(time):
		date_join = datetime.datetime.strptime(str(time), "%Y-%m-%d %H:%M:%S.%f")
		date_now = datetime.datetime.now(datetime.timezone.utc)
		date_now = date_now.replace(tzinfo=None)
		since_join = date_now - date_join

		m, s = divmod(int(since_join.total_seconds()), 60)
		h, m = divmod(m, 60)
		d, h = divmod(h, 24)

		if d > 0:
			msg = "{0}d {1}h ago"
		elif d == 0 and h > 0:
			msg = "{1}h {2}m ago"
		elif d == 0 and h == 0 and m > 0:
			msg = "{2}m {3}s ago"
		elif d == 0 and h == 0 and m == 0 and s > 0:
			msg = "{3}s ago"
		else:
			msg = ""
		return msg.format(d, h, m, s)


	@commands.command(aliases=['about', 'botinfo'])
	@commands.guild_only()
	@commands.bot_has_permissions(embed_links=True)
	async def info(self, ctx):
		"""info about the bot and its guild status!"""
		self.bot.website = 'https://dragdev.xyz'
		async with ctx.channel.typing():
			c = len(list(self.bot.get_all_channels()))
			m = ctx.guild.me
			e = discord.Embed(title="My Info!", url='https://invite.gg/ebot', color=discord.Color.blurple())
			e.add_field(name="Stats:", value=f"Guilds: {len(self.bot.guilds)}\nChannels: {c}\nUsers: {len(self.bot.users)}"
						f"\nCreator: {self.bot.get_user(self.bot.owner_id).mention} ("
						f"{self.bot.get_user(self.bot.owner_id).name})\nlib: discord.py {discord.__version__}\n"
						f"Commands executed: {self.commanded}\n"
						f"Messages since last reload: {self.recieved}")
			e.add_field(name="Guild Info:", value=f"{'no nick' if m.nick is not None else f'Nick: {m.nick}'}"
												f"\ntop role: {m.top_role.mention}\nJoined on: `"
												f"{m.joined_at.strftime(self.dtf)}`\n", inline=False)
			e.add_field(name="meta:", value=f"[bot lists removed]\n\n[**Website: https://dragdev.xyz**]({self.bot.website})")
		await ctx.send(embed=e)

	@commands.command()
	async def charinfo(self, ctx, *, characters: typing.Union[discord.Emoji, str] = '\u200B'):
		"""Shows you information about a number of characters.
		no spam pls
		"""
		if isinstance(characters, discord.Emoji):
			cmd = self.bot.get_command('ei')
			return await ctx.invoke(cmd, emoji=characters)
		def to_string(c):
			digit = f'{ord(c):x}'
			name = unicodedata.name(c, 'Name not found.')
			return f'`\\U{digit:>08}`: {name} - {c}'
		msg = '\n'.join(map(to_string, characters))
		if len(msg) > 2000:
			for p in pagify(msg):
				await ctx.send(p)
			return
		await ctx.send(msg)

	@commands.command(aliases=["cinfo", "ci"])
	@commands.guild_only()
	async def channelinfo(self, ctx, channel: discord.TextChannel = None):
		"""Get a text channel's info. wip."""
		from utils.formatting import Humanreadable as hr
		if channel is None:
			channel = ctx.channel
		e = discord.Embed(title=f"{channel.name}'s info!", color=ctx.author.color)
		e.description = f"**Name**: {channel.name}\n**ID**: {channel.id}\n**Category**: {channel.category.name}\n" \
			f"**Channel Topic**: {channel.topic}\ncreated {hr.dynamic_time(channel.created_at)}\n**Users who can see it**: {len(channel.members)}"
		return await ctx.send(embed=e)

	@staticmethod
	async def fixtime(d, h, m, s):
		if s == 1:
			ss = f'{s} second!'
		else:
			ss = f"{s} seconds!"
		if d > 0:
			return f"{d} days, {h} hours, {m} minutes and {ss}!"
		elif d < 1 and h > 0:
			return f"{h} hours, {m} minutes and {ss}"
		elif d < 1 and h < 1 and m > 0:
			return f"{m} minutes and {ss}"
		elif d < 1 and h < 1 and m < 1 and s > 1:
			return f'{ss}'
		else:
			return f"{d} days, {h} hours, {m} minutes and {ss}"


	@commands.command()
	@commands.cooldown(1, 3, commands.BucketType.user)
	async def uptime(self, ctx):
		"""Get the bots total uptime"""
		difference = int(round(time.time() - self.bot.total_uptime))

		seconds = difference % 60
		minutes = round(difference / 60)
		hours = round(difference / 3600)
		days = round(difference / 84600)

		while minutes < 0:
			minutes = 0
		while seconds > 59:
			seconds -= 60
			minutes += 1
		while minutes > 59:
			minutes -= 60
			hours += 1
		while hours > 23:
			hours -= 24
			days += 1
		if days < 1 and hours < 1 and minutes < 3:
			await ctx.send(
				f"I have been online for: {days} days, {hours} hours, {minutes} minutes and {seconds} seconds!\n"
				f"I have probably just rebooted")
		else:
			await ctx.send(
				f"I have been online for: {days} days, {hours} hours, {minutes} minutes and {seconds} seconds!")


	@commands.Cog.listener()
	async def on_member_join(self, m):
		if m.id == 269340844438454272 and m.guild.id == 486910899756728320:  # for a special someone
			r = discord.utils.get(m.guild.roles, name='Retired Dev')
			await m.add_roles(r)
		# 538410984411234324
		if m.id == 421698654189912064 and m.guild.id == 486910899756728320:
			r = discord.utils.get(m.guild.roles, name="Developer")
			await m.add_roles(r)



def setup(bot):
	bot.add_cog(MainCog(bot))
