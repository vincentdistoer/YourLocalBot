import asyncio
import datetime
import json
import logging as logger
import os
import random
import typing
from random import randint
import praw
import aiohttp
import discord
from discord.ext import commands, tasks
import time
from utils import checks
from utils.errors import InvalidFramework
from utils.escapes import *
from utils.formatting import Humanreadable
from cogs.config import json_mngr

log = logger.getLogger(__name__)

def can_purge_self(ctx):
	u = ctx.author
	return u.guild_permissions.manage_messages or ctx.author.id == ctx.bot.owner_id

class Ships:

	@classmethod
	def do_embed(cls, name: str, desc: str, info: dict):
		e = discord.Embed(
			title=name,
			description=f"{desc}\nHull/Shield: {info['hull']}/{info['shield']}",
			color=discord.Color.blue()
		)
		lasers = info['lasers']
		e.add_field(name=f"Lasers: {len(info['lasers'])}", value=f"Small: {lasers['small']}\nMedium: {lasers['med']}\n"
		f"Large: {lasers['large']}")
		e.set_thumbnail(url=info['img_url'])
		e.set_footer(text="NOT ship selection || react with \U000025c0 and \U000025b6 to navigate!")
		return e

	@staticmethod
	def default():
		t = {
			"hull": 250,
			"shield": 100,
			"lasers": {"small": 1, "med": 0, "large": 0},
			"drills": 1,
			"fighters": 0,
			"img_url": 'https://i.postimg.cc/c4sGXF1K/8-C6-A8741-A894-49-CA-AE37-D8-B01-E47-D471.jpg'
		}
		embed = Ships.do_embed("default", "*default ship. pretty sh\*t.*", t)
		t['embed'] = embed
		return t

	@staticmethod
	def carrier():
		t = {
			"hull": 1000,
			"shield": 100,
			"lasers": {"small": 2, "med": 1, "large": 2},
			"drills": 0,
			"fighters": 12,
			'img_url': 'https://cdn.discordapp.com/attachments/563380919113613332/580422480565633024/image0.png'
		}
		embed = Ships.do_embed("carrier-class cruizer", "*this behemoth of a ship carries an impressive armament of "
														"lasers, however sacrificing shield power.*", t)
		t['embed'] = embed
		return t

	@staticmethod
	def fighter():
		t = {
			"hull": 20,
			"shield": 50,
			"lasers": {"small": 3, "med": 0, "large": 0},
			"drills": 0,
			"fighters": 0,
			'img_url': 'http://orig07.deviantart.net/e92d/f/2012/296/2/7/starfighter_one_by_meckanicalmind-d5ios8k.jpg'
		}
		ebed = Ships.do_embed("fighter", "*nothing special, just a small fighter.*", t)
		t['embed'] = ebed
		return t

class bw:

	@staticmethod
	def bad_words():
		return ['nigger', 'nig', 'cunt', 'discord.gg', 'd i s c o r d . g g']
class Developing_Commands(commands.Cog):

	def __init__(self, bot):
		self.bot = bot
		self.success = 'success:522078924432343040'
		self.loading = 'a:loading20:553253741311295498'
		self.error = 'fail:522076877075251201'
		self.dtf = "%I:%M %p @ %d/%m/%Y %Z"
		self.session = aiohttp.ClientSession()
		self.snipes = {}
		self.gc_locked = []
		self.ratelimit = []
		self.cloning = {}
		self.cache = {}
		self.cacheclearrer.start()
		self.cache['gc'] = json_mngr.read('./data/gcb.json')
		self.donator = discord.utils.get(discord.utils.get(self.bot.guilds,id=486910899756728320).roles ,name="Donator")
		self.ss = discord.utils.get(discord.utils.get(self.bot.guilds,id=486910899756728320).roles ,name="Support")

	@tasks.loop(seconds=90)
	async def cacheclearrer(self):
		self.cache = {}
		self.cache['gc'] = json_mngr.read('./data/gcb.json')


	async def do_ratelimit(self, user):
		self.ratelimit.append(user.id)
		await asyncio.sleep(2.5)
		self.ratelimit.remove(user.id)

	@commands.group()
	@checks.gcmod()
	async def gclock(self, ctx, *, user: discord.User):
		"""Lock a user from using the global chat."""
		self.gc_locked.append(user.id)
		await ctx.send(f"ok then. {user.id} has been added to the list of locked users.")

	@commands.command()
	@checks.gcmod()
	async def gcunlock(self, ctx, user: discord.User):
		"""unlock a user from the global chat"""
		self.gc_locked.append(user.id)
		await ctx.send(f"ok, {user.id} was removed from the list\nLocked users:\n```\n{' / '.join(self.gc_locked)}\n```")

	@commands.command(hidden=True)
	@checks.gcadmin()
	async def gcban(self, ctx, user: discord.User, *,reason: commands.clean_content):
		"""ban someone from using the global chat"""
		data = json_mngr.read('./data/gcb.json')
		if str(user.id) in data.keys():
			return await ctx.send(f"that user is already banned, for {data[str(user.id)][0]}")
		data[str(user.id)] = [reason, ctx.author.id]
		json_mngr.handle_modify('./data/gcb.json', newdata=data, indent=2, backup=True)
		await ctx.message.add_reaction(self.success)

	@commands.command(hidden=True)
	@checks.gcadmin()
	async def gcunban(self, ctx, user: discord.User):
		"""ban someone from using the global chat"""
		data = json_mngr.read('./data/gcb.json')
		if str(user.id) not in data.keys():
			return await ctx.send(f"that user is not banned! are they just locked?")
		del data[str(user.id)]
		json_mngr.handle_modify('./data/gcb.json', newdata=data, indent=2, backup=True)
		await ctx.message.add_reaction(self.success)

	@gcban.after_invoke
	@gcunban.after_invoke
	async def dasdasdadas(self, ctx):
		self.cache['gc'] = json_mngr.read('./data/gcb.json')

	@commands.command()
	@commands.bot_has_permissions(embed_links=True)
	async def afk(self, ctx, *, reason: str = None):
		"""un/mark yourself as afk"""
		for x in os.listdir('./data/afks'):
			if str(ctx.author.id) == x:
				if reason is None:
					os.remove(f'./data/afks/{x}')
					return await ctx.send('welcome back!', delete_after=15)
				else:
					old_reason = ""
					with open(f'./data/afks/{str(ctx.author.id)}', 'r+') as x:
						old_reason += ''.join(x.readlines())
						with open(f'./data/afks/{str(ctx.author.id)}', 'w+') as z:
							x.write(reason)
							x.close()
					e = discord.Embed(description=f"Old: {old_reason}\nNew: {reason}", color=discord.Color.orange())
					return await ctx.send("Updated your AFK Status:", embed=e)
		else:
			with open(f'./data/afks/{str(ctx.author.id)}', 'w+') as x:
				if reason:
					x.write(reason)
				else:
					pass
				x.close()
				return await ctx.send("you're now marked as afk.", delete_after=15)

	@commands.command(name='amiafk?')
	async def amiafk(self, ctx):
		"""Check if your afk"""
		for m in os.listdir('./data/afks'):
			if m.startswith(str(ctx.author.id)):
				return await ctx.send("You are currently AFK")
		else:
			return await ctx.send("You are not currently marked as AFK.")

	@commands.command(hidden=True)
	async def gcrules(self, ctx):
		x = "No spamming\nNo links\nNo NSFW\nNo ads\nNo doxxing\nNo drama\nKeep cursing to a minimum\nNo invisible/broken names/nicks.\nNo Formatting abuse"
		y = x.split('\n')
		ffmt = ""
		for n, r in enumerate(y, start=1):
			ffmt += f"{n}: {r}\n"
		e = discord.Embed(title="Global Chat rules.", description=ffmt, color=discord.Color.blue())
		await ctx.send(embed=e)

	def get_global_rank(self, author):
		ss = discord.utils.get(self.bot.guilds, id=486910899756728320)
		roles_ids = [566471715513958400, 566471697679777802, 566471677941121025, 566471635591233538]
		roles = [discord.utils.get(ss.roles, id=r) for r in roles_ids]
		if author in ss.members:
			for role in roles:
				if author in role.members:
					return True
				else:
					continue

		else:
			return False
	@commands.Cog.listener()
	async def on_message(self, m):
		owners = {
			179049652606337024: "BxPanxi",
			421698654189912064: "EEk",
			291933031919255552: "Penguin113",
			493790026115579905: "Elemental",
			344878404991975427: "chromebook777",
			414746664507801610: "Scientific Age",
			293066151695482882: "inside dev"
		}
		if m.author.id in list(self.bot.locked_out):
			return
		ctx = m
		message = m
		if ctx.author.bot:
			return
		if ctx.channel.name == 'ylb-gc' or 'ylb-gc' in str(ctx.channel.topic).lower():
			if str(m.author.id) in self.cache['gc']:
				return  # banned
			if m.author.id in self.cache.keys():
				pass
			else:
				self.cache[m.author.id] = self.get_global_rank(m.author)
			p = dict(ctx.guild.me.guild_permissions)
			if p['manage_messages'] and p['send_messages'] and p['add_reactions'] and p['external_emojis']:
				X = self.bot.get_channel(591798452002750466)
				await X.send(f'{ctx.guild.id} : {ctx.author}~{ctx.author.id} \n> {ctx.clean_content}')
				cn = ctx.clean_content
				# nsfw bot ban
				if '81ZH2Y' in cn.upper() or 'QYHhZv' in cn.upper():
					return await ctx.channel.send(f"<:{self.error}> this url is being used in nsfw raidbots. your"
												  f" message has not been sent.")
				if ctx.author.id in self.ratelimit:
					return await ctx.channel.send(f"<:{self.error}> You are on cooldown! try again in a few seconds.")
				self.bot.loop.create_task(self.do_ratelimit(ctx.author))
				await ctx.add_reaction(self.loading)
				for c in self.bot.guilds:
					for x in c.text_channels:
						if x.name == 'ylb-gc' or 'ylb-gc' in str(x.topic).lower():
							whitespace = '\u200B'
							content = discord.utils.escape_mentions(message.clean_content)
							content = content.replace('\n', '\n> ')
							nickname = discord.utils.escape_mentions(discord.utils.escape_markdown(message.author.nick)) if message.author.nick else None
							ann_mode = False
							if ctx.author.id == 421698654189912064 and content.startswith('! '):
								content.replace('! ', '', 1)
								ann_mode = True
							name = discord.utils.escape_mentions(discord.utils.escape_markdown(message.author.name))
							if not ann_mode:
								content = content.replace('https', '#####').replace('http', '####').replace('://', '###')\
									.replace('//', '##').replace('.gg', '###').replace('nig', '###')
							end_message = f"**{name} {f'({nickname})' if nickname else ''}:** {content}"
							if ctx.author in self.donator.members:
								end_message = f"<:realcoin:606459545606291471> **{name} {f'({nickname})' if nickname else ''}:** {content}"
							if ctx.author in self.ss.members:
								end_message = f"💬 **{name} {f'({nickname})' if nickname else ''}:** {content}"
							if self.cache[ctx.author.id]:
								end_message = f"<:{self.success}> **{name} {f'({nickname})' if nickname else ''}:** {content}"
							else:
								pass
							if ctx.author.id == self.bot.owner_id:
								end_message = f"<:owner:604455033831948291> **{name} {f'({nickname})' if nickname else ''}:** {content}"
							elif ctx.author.id in owners.keys():
								end_message = f"<:coowner:606442352973971467> **{name} {f'({nickname})' if nickname else ''}:** {content}"
							try:
								await x.send(end_message)
							except:
								continue
							await asyncio.sleep(0.25)
				await ctx.add_reaction(self.success)
				await ctx.delete(delay=0.5)
			else:
				await ctx.channel.send(f"<:{self.error}> I need **send messages**, **read messages**,"
									   f" **manage messages**, **add reactions** and **use external emojis**"
									   f" for global chat to work!**", delete_after=30)

	@commands.Cog.listener(name='on_message')
	async def on_afk_msg(self, m):
		if m.author.bot:
			return
		for x in os.listdir('./data/afks'):
			for y in m.mentions:
				if str(y.id) == x:
					try:
						mmm = discord.Color.blurple() if y.color is discord.Color.default() else y.color
					# not sure why it would fail, but i have one thing in mind
					except:
						mmm = discord.Color.greyple()
					e = discord.Embed(title=f'{y.display_name} is afk!', color=mmm)
					with open(f'./data/afks/{x}', 'r') as t:
						if t.readlines is not []:
							aa = t.readlines()

							for aaa in aa:
								reason = aaa
								e.description = 'reason: {}'.format(
									reason
								)
						else:
							pass
					return await m.channel.send(embed=e,
												delete_after=60)

	@commands.Cog.listener()
	async def on_message_delete(self, m):
		if m.author.bot:
			return
		if str(m.guild.id) not in self.snipes:
			self.snipes[str(m.guild.id)] = {}
		self.snipes[str(m.guild.id)][str(m.channel.id)] = m

	@afk.after_invoke
	async def finisher(self, ctx):
		await asyncio.sleep(15)
		await ctx.message.delete()

	# purge


	def findcategory(self, ctx, reply):
		for c in ctx.guild.categories:
			if str(c.id) == reply.content or c.name == reply.content:
				cat = c
				return cat
		else:
			return False

	@commands.command()
	@commands.guild_only()
	@commands.bot_has_permissions(
		manage_messages=True,
		add_reactions=True,
		external_emojis=True,
		embed_links=True
	)
	async def say(self, ctx, *, text: commands.clean_content):
		"""
		make the bot repeat what you say!

		flags:
		• --embed: makes the message an embed [see pollbed]
		• --poll: reacts with tick and cross [see pollbed]
		• --pollbed: used for having a poll embed. this is a placeholder until i figure out why the --embed flag wont remove --poll
		"""
		await ctx.message.delete()
		content = escape(text, mass_mentions=True, formatting=False, urls=True, invites=True)
		embed = False
		poll = False
		if '--pollbed' in content:
			content = content.strip('--pollbed')
			embed = True
			poll = True
		else:
			if '--poll' in content:
				content = content.replace('--poll', '')
				poll = True
			if '--embed' in content:
				content = content.replace('--embed', '', 1)
				embed = True
		e = discord.Embed(description=content, color=ctx.author.color)
		e.set_author(icon_url=ctx.author.avatar_url, name=ctx.author)
		content = ctx.author.name + "#" + ctx.author.discriminator + " **»** " + content
		if embed:
			m = await ctx.send(embed=e)
		else:
			m = await ctx.send(content)
		if poll:
			await m.add_reaction(self.success)
			await m.add_reaction(self.error)

	@commands.command(aliases=['cat', 'aww', 'cats:tm:'])
	@commands.bot_has_permissions(embed_links=True)
	@commands.cooldown(1, 5, commands.BucketType.default)
	async def cats(self, ctx):
		"""Shows a cat"""
		search = "https://nekos.life/api/v2/img/meow"
		try:
			async with self.session.get(search) as r:
				result = await r.json()
				r.close()
			resp = ['Your cat, sir/madam', 'your cat picture is served.', 'oh look! a cute one!',
					'i think the cuteness of that cat made my cpu melt', '<3', 'as requested',
					'Cats:tm: - since 2019', 'cats are the best']
			e = discord.Embed(title=random.choice(resp), url=result['url'], color=ctx.author.color)
			e.set_image(url=result['url'])
			await ctx.send(embed=e)
		except:
			await ctx.send("Couldn't Get An Image.. sorry v.v")


	@commands.group(aliases=['ghost'], invoke_without_command=True)
	async def snipe(self, ctx, channel: discord.TextChannel = None):
		"""Get the last deleted medsage
		mention a channel to get it's message
		subcommands.
		"""
		if ctx.guild.id == 0:
			return await ctx.send('This command has been blocked by the server owner')
		g = str(ctx.guild.id)
		channel = ctx.channel if channel is None else channel
		c = str(channel.id)
		if g not in self.snipes:
			return await ctx.send('No recent snipes have been recorded for this guild!')
		if c not in self.snipes[g]:
			return await ctx.send('No recent snipes have been recorded for {.mention}!'.format(channel))
		m = self.snipes[g][c]
		e = discord.Embed(description=m.content, color=m.author.color)
		e.set_author(icon_url=m.author.avatar_url, name=m.author)
		e.title = random.choice(['NoScoped', 'Sniped', 'HeadShot'])
		await ctx.send(embed=e)

	@snipe.command(name='raw')
	@commands.cooldown(1, 90, commands.BucketType.user)
	@checks.admin_or_permissions(manage_guild=True)
	async def __raw(self, ctx):
		"""Return the raw Snipes Data."""
		from utils.page import pagify
		stuff = str(self.snipes)
		for page in pagify(stuff):
			await ctx.send(page)

	@commands.command(name="colour", aliases=["color"])
	@checks.is_admin()
	async def editrole(self, ctx, roles: commands.Greedy[discord.Role], *, color: discord.Color = 'blue'):
		"""Edit any role's color! I must be above The role"""
		for role in roles:
			if role >= ctx.guild.me.top_role:
				return await ctx.send('role {} too high'.format(role.name))
		for role in roles:
			await role.edit(color=color, reason=f"invoked by {ctx.author}")
		await ctx.send('done.')

	@staticmethod
	def conv_time(s, m=0, h=0):
		while s >= 60:
			m += 1
			s -= 60
		while m >= 60:
			h += 1
			m -= 60
		if h > 0:
			return f'{h}h, {m}m and {s}s.'
		elif h == 0 and m > 0:
			return f'{m}m and {s}s.'
		elif h == 0 and m == 0 and s > 0:
			return f'{s}s.'

	@commands.group(name='cloneguild', aliases=['cg', 'clone', 'clone_guild', 'clone_server', 'cs', 'cloneserver'], invoke_without_command=True)
	async def clone_guild(self, ctx, your_servers_invite: discord.Invite, max_msgs: typing.Optional[int], no_ping:bool=False):
		"""
		clone a guild's channels into one of your own
		"""
		max_msgs = max_msgs if max_msgs else 1000
		if isinstance(your_servers_invite.guild, discord.PartialInviteGuild):
			return await ctx.send("I must be in the guild you want me to clone it into!")
		if not your_servers_invite.guild.me.guild_permissions.administrator:
			return await ctx.send(f"I need admin in {str(your_servers_invite.guild)}")
		if your_servers_invite.guild.owner != ctx.author:
			return await ctx.send("You must own that server!")
		if your_servers_invite.guild.member_count > 5 and not no_ping:
			return await ctx.send("You must have less then 5 members or have enabled no_ping.")
		mm = max_msgs if max_msgs>0 else 0
		eta = self.conv_time((len(ctx.guild.channels) + len(ctx.guild.roles) + mm) * 2)
		task_id = len(self.cloning.keys()) + 1
		self.cloning[task_id] = time.time()
		msg = await ctx.send(f"Cloning:```\n"
							f"{len(ctx.guild.channels)} channels\n{1000 * len(ctx.guild.text_channels)}"
						f" messages\n{len(ctx.guild.roles)} roles```\n\nThis could take a while"
						f". i will DM/ping you when it is "
						f"complete {ctx.author.mention}\n**Estimated time until completion:** "
						f"{eta}.\n\n*you can cancle the process by kicking me from {str(your_servers_invite.guild)}")
		guild = your_servers_invite.guild
		for channel in guild.channels:
			await channel.delete(reason="Cleansing")
		for role in guild.roles:
			try:
				await role.delete()
			except:
				pass
		for role in reversed(ctx.guild.roles):
			await guild.create_role(name=role.name, permissions=role.permissions, color=role.color, hoist=role.hoist,
									mentionable=role.mentionable)
		if len(ctx.guild.categories) == 0:
			for channel in ctx.guild.channels:
				if isinstance(channel, discord.TextChannel):
					tc = channel
					pc = await guild.create_text_channel(tc.name, position=tc.position, topic=tc.topic,
														 slowmode_delay=tc.slowmode_delay, nsfw=tc.is_nsfw())
					try:
						for thing, value in dict(pc.overwrites):
							try:
								await pc.set_permissions(thing, overwrite={thing: value})
							except:
								continue
					except:
						pass
					await asyncio.sleep(2)
					try:
						async for msg in tc.history(limit=max_msgs, oldest_first=True):
							e = '\u200B'
							if len(msg.embeds) == 0:
								_embed = [None]
							else:
								_embed = msg.embeds

							await pc.send(f"**{msg.author.display_name}** {msg.created_at.strftime('%d/%m/%y')}:\n"
										  f"{msg.content if not no_ping else msg.content.replace('@', e)}\n", embed=_embed[0])
							await asyncio.sleep(1)
					except:
						continue
				else:
					jc = await guild.create_voice_channels(channel.name, bitrate=channel.bitrate,
														   user_limit=channel.user_limit)
					try:
						for thing, value in dict(channel.overwrites):
							try:
								await jc.set_permissions(thing, overwrite={thing: value})
							except:
								continue
					except:
						pass
		for category in ctx.guild.categories:
			cat = await guild.create_category(category.name, overwrites=category.overwrites)
			await asyncio.sleep(2)
			for tc in category.text_channels:
				pc = await cat.create_text_channel(tc.name, position=tc.position, topic=tc.topic,
												   slowmode_delay=tc.slowmode_delay, nsfw=tc.is_nsfw())
				try:
					for thing, value in dict(pc.overwrites):
						try:
							await pc.set_permissions(thing, overwrite={thing: value})
						except:
							continue
				except:
					pass
				await asyncio.sleep(2)
				try:
					if tc.permissions_for(ctx.author).read_messages and tc.permissions_for(ctx.author).read_message_history:
						async for msg in tc.history(limit=max_msgs, oldest_first=True):
							e = '\u200B'
							if len(msg.embeds) == 0:
								_embed = [None]
							else:
								_embed = msg.embeds

							await pc.send(f"**{msg.author.display_name}** {msg.created_at.strftime('%d/%m/%y')}:\n"
										  f"{msg.content if not no_ping else msg.content.replace('@', e)}\n", embed=_embed[0])
							await asyncio.sleep(1)
				except:
					continue
			for vc in category.voice_channels:
				jc = await cat.create_voice_channel(vc.name, bitrate=vc.bitrate, user_limit=vc.user_limit)
				try:
					for thing, value in dict(vc.overwrites):
						try:
							await jc.set_permissions(thing, overwrite={thing: value})
						except:
							continue
				except:
					pass
		await guild.edit(name=ctx.guild.name)
		try:
			await ctx.author.send(f"Your guild clone was successful")
		except:
			await ctx.send(f"{ctx.author.mention} your clone completed.")
		finally:
			await msg.delete()

	@clone_guild.group(enabled=False)
	@checks.gowner()
	async def fromtemplate(self, ctx, *,template: commands.clean_content = 'List'):
		"""
		create a server from some pre-defined templates!
		`template` can be a name of a template, or `list` to list available templates!
		can also be `info` to view info on a template
		"""
		templates = json_mngr().read('./data/templates.json')
		if str(template).lower().startswith('li'):  # lazily assume its list
			e = discord.Embed(title="Templates:")
			for templ in templates.keys()[:24]:  # shows up to 24 templates
				e.add_field(name=f"Name: {templ['name']}", value=f"Author: {templ['author']}\nTheme: {templ['theme']}" \
					f"\nText Channels: {len(templ['textchannels'])}\nVoice Channels: "
				f"{len(templ['voicechannels'])}", inline=False)
			return await ctx.send(embed=e)
		if str(template).lower() not in [s.lower() for s in templates.keys()]:
			return await ctx.send(f"{template} is not a registered template!\nWant to add it? do `"
								  f"{ctx.prefix}clone fromtemplate create`!\nWant to see a"
								  f" list of templates? do `{ctx.prefix}clone fromtemplate list`!")
		c = lambda m: m.author==ctx.author and m.channel==ctx.channel
		t = templates[str(template).lower()]
		try:
			msg = await ctx.send(f"Please confirm you would like to use the template `{template}` [y/n]"
								 f"\n```\nImporting:\n{len(t['textchannels'])} Text Channels\n"
								 f"{len(t['voicechannels'])} Voice Channels\n{len(t['roles'])} roles\n```\n**REMEMBE"
								 f"R THIS WIPES YOUR SERVER FIRST**")
			mr = await self.bot.wait_for('message', check=c, timeout=120)
			if mr.content.lower().startswith('y'):
				pass
			else:
				return await msg.edit(content="ok. cancelled.")
		except asyncio.TimeoutError:
			return await ctx.send("Timed out. assumed answer: n")
		for i in range(5, 0):
			if ctx.guild.me.top_role != list(reversed(ctx.guild.roles))[0]:
				await msg.edit(content=f"Please give me the highest role in this server first.\nRetries remaining: "
				f"{5 - i}")
				await asyncio.sleep(10)
			else:
				break
		else:
			return await msg.edit(content="I require the highest role to preform this action")

		await msg.edit("ok.")
		err = []
		for channel in ctx.guild.channels:
			try:
				await channel.delete(reason="Forming Template")
			except Exception as e:
				err.append(e)
				continue
		for role in ctx.guild.roles:
			try:
				await role.delete(reason="Forming template")
			except Exception as e:
				err.append(e)

		for role in t['roles']:
			try:
				await ctx.guild.create_role(name=role['name'], permissions=role['permissions'], color=role['color'],
											hoist=role['hoist'], mentionable=role['mentionable'], reason="Importing roles")
			except Exception as e:
				err.append(f"Error while creating role {role.id}: {e}")
		for category in t['categories']:
			await ctx.guild.create_category(category.name, )
		for textchannel in t['textchannels']:
			if textchannel.category is None:
				await ctx.guild.create_text_channel(textchannel['nname'], overwrites=textchannel['overwrites'],
													topic=textchannel['topic'], slowmode_delay=textchannel['slowmode_delay'],
													nsfe=textchannel['nsfw'], reason="No category channel imports")

	@commands.command(hidden=True)
	@checks.gowner()
	async def backup(self, ctx, *, tobackup: typing.Optional[int], channel: discord.TextChannel=None):
		data = json_mngr.read('./data/backups.json')
		if tobackup is None:
			tobackup = 100
		if not channel:
			data[str(ctx.guild.id)] = {}
			for channel in ctx.guild.text_channels:
				data[str(ctx.guild.id)][str(channel.name)] = []
				async for x in channel.history():
					pass



def setup(bot):
	logger.info('Loaded dev module')
	bot.add_cog(Developing_Commands(bot))
