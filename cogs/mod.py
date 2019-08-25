import discord, os, asyncio, datetime, random, time
from discord.ext import commands
from utils import checks
from utils.escapes import *
from utils import *
from utils import page
import typing
from cogs.config import json_mngr
import json
import re
def can_purge_self(ctx):
	u = ctx.author
	return u.guild_permissions.manage_messages or ctx.author.id == ctx.bot.owner_id
class gid:
	def __init__(self, id):
		self.id = id

	def __str__(self):
		return f'{self.id}'
class Mod(commands.Cog):

	def __init__(self, bot):
		self.bot = bot
		self.success = '<:success:522078924432343040>'
		self.loading = '<a:loading20:553253741311295498>'
		self.error = '<:fail:522076877075251201>'
		self.dtf = "%I:%M %p @ %d/%m/%Y %Z"
		self.silenced_errors = (discord.Forbidden, discord.NotFound, discord.HTTPException)

	def fromtimestamp(self, ts):
		return datetime.datetime.strptime(ts, '%Y-%m-%d %H:%M:%S.%f')

	#  kick

	def setup(self, guild_id: str):
		data = json_mngr.read('./data/logs.json')
		data[guild_id] = {
			"warns": {},
			"mutes": {},
			"unmutes": {},
			"kicks": {},
			"bans": {},
			'id': 0
		}
		json_mngr.handle_modify('./data/logs.json', newdata=data, indent=2, backup=True)

	async def setup_mute(self, ctx, role: discord.Role):
		for channel in ctx.guild.text_channels:
			rm = channel.overwrites_for(role).send_messages
			if rm:
				await channel.set_permissions(role, send_messages=False, add_reactions=False, reason=f'Muted role setup'
				f' by {ctx.author}')
			continue
		for channel in ctx.guild.voice_channels:
			rm = channel.overwrites_for(role).connect
			if rm:
				await channel.set_permissions(role, connect=False, reason=f'Muted role setup'
				f' by {ctx.author}')
			continue
		return True

	@staticmethod
	async def check_role_heirchy(a, b):
		if a.top_role >= b.top_role:
			return True

	@staticmethod
	def check_heirerchy(a, b):
		if a > b:
			return True

	@staticmethod
	def read(fp: str='./data/logs.json'):
		with open(fp, 'r') as x:
			y = json.load(x)
		return y

	def add(self, *, mode:str='warn', data:dict):
		with open('./data/logs.json', 'r') as backup:
			backup_data = json.load(backup)
		with open(f'./data/logs.json', 'w+') as x:
			try:
				print(data)
				json.dump(data, x, indent=2)
			except Exception as e:
				json.dump(backup_data, x)
				print(str(e))
				return e.__traceback__
		return True


	@commands.command()
	@commands.has_permissions(ban_members=True)
	@commands.bot_has_permissions(ban_members=True)
	async def ban(self, ctx, users: commands.Greedy[typing.Union[discord.Member, discord.User, int]], *, reason: commands.clean_content):
		"""ban people! takes a list of users and ints, then moves on to reason."""
		role = discord.utils.get(discord.utils.get(ctx.bot.guilds, id=486910899756728320).roles, id=576468481562640426)
		if len(users) >= 10 and ctx.author not in role.members:
			await ctx.send("Mass-banning 10+ users is restricted to premium users, to avoid delays and ratelimits."
						   " I will ban the first 10 listed accounts.\n*Don't want this message? get premium today!"
						   " `y!getpremium`*", delete_after=5)
			users = users[:10]
		banned = []
		for user in users:
			if isinstance(user, int):
				user = await self.bot.fetch_user(user)
				await ctx.guild.ban(user, reason=reason)
				banned.append(user.display_name)
			elif isinstance(user, discord.Member):
				if user.top_role >= ctx.guild.me.top_role or user.top_role >= ctx.author.top_role:
					continue
				else:
					await user.ban(reason=reason)
					banned.append(user.display_name)
			else:
				await ctx.guild.ban(user, reason=reason)
		await ctx.send(f'successfully banned {len(banned)} ({", ".join(banned)}) for: {reason}')

	@commands.command()
	@commands.has_permissions(kick_members=True)
	@commands.bot_has_permissions(kick_members=True)
	async def kick(self, ctx, users: commands.Greedy[discord.Member], *, reason: commands.clean_content):
		"""kick people! takes a list of users and ints, then moves on to reason."""
		role = discord.utils.get(discord.utils.get(ctx.bot.guilds, id=486910899756728320).roles, id=576468481562640426)
		if len(users) >= 10 and ctx.author not in role.members:
			await ctx.send("Mass-kicking 10+ users is restricted to premium users, to avoid delays and ratelimits."
						" I will ban the first 10 listed accounts.\n*Don't want this message? get premium today!"
						" `y!getpremium`*", delete_after=5)
			users = users[:10]
		banned = []
		for user in users:
			if isinstance(user, int):
				user = await self.bot.fetch_user(user)
				await user.kick(reason=reason)
				banned.append(user.display_name)
			else:
				if user in ctx.guild.members:
					if user.top_role >= ctx.guild.me.top_role or user.top_role >= ctx.author.top_role:
						continue
					else:
						await user.kick(reason=reason)
						banned.append(user.display_name)
		await ctx.send(f'successfully kicked {len(banned)} ({", ".join(banned)}) for: {reason}')

	@commands.command(brief='DM users in a role. args are displayed on y!help roledm')
	@commands.has_permissions(administrator=True)
	@commands.guild_only()
	async def roledm(self, ctx, role: commands.Greedy[discord.Role], *, text: str):
		"""DM users in a role.
		{0} = user
		{1} = guild name
		{2} = you
		{3} = their role
		{4} = invoking channel {this channel}
		{ctx} = commands.Context -> really advanced.
		**THESE ARGUMENTS ARE ADVANCED!** If you don't know how to use them, don't."""
		sent = []
		for x in ctx.guild.members:
			for z in role:
				if z in x.roles:
					try:
						await x.send(text.format(x, ctx.guild, ctx.author, z, ctx.channel,
												 ctx=ctx))
					except discord.Forbidden:
						pass
					finally:
						break
		await ctx.send('done')

	@commands.command(hidden=True)
	@commands.has_permissions(ban_members=True)
	async def pban(self, ctx, user: discord.User, *, reason='No reason provided!'):
		"""\"ban\" some users!"""
		await ctx.message.delete()
		await ctx.send(f'***<:success:522078924432343040> banned {user.name} for {reason}***')

	@commands.command()
	@checks.admin_or_permissions(manage_guild=True, manage_messages=True, manage_channels=True)
	async def transfer(self, ctx, delete: typing.Optional[bool], message: discord.Message, to: discord.TextChannel, no_ping: bool = False):
		"""transfer a message from one channel to another!"""
		delete=delete if delete is not None else True
		if not dict(to.permissions_for(ctx.guild.me))['send_messages'] and not dict(to.permissions_for(ctx.guild.me))['embed_links']:
			return await ctx.send(f"I can't send messages to {to.mention}!")
		if not message.author.bot and message.author != ctx.author:
			return await ctx.send("You can only move messages by bots or by yourself!")
		try:
			m = await ctx.send("Copying content...")
			if no_ping or not dict(to.permissions_for(ctx.author))['mention_everyone']:
				message.content = message.clean_content
			if message.author != self.bot.user:
				message.content = f"*transferred*\n{message.content}"
			embed = message.embeds[0] if len(message.embeds) > 0 else None
			await m.edit(content="Sending to channel..")
			await to.send(message.content, embed=embed)
			if delete:
				await message.delete(delay=1)
			await m.edit(content="Success!")
		except Exception as e:
			await ctx.send(f"Unhandled error: `{e}`")

	@commands.group(invoke_without_command=True)
	@checks.mod_or_permissions(manage_messages=True)
	@commands.bot_has_permissions(manage_messages=True)
	@commands.guild_only()
	async def purge(self, ctx, user: typing.Optional[discord.User], amount: int = 50):
		"""Purge messages"""
		if ctx.invoked_subcommand is not None:
			return
		check=None
		if user is not None:
			def check(m):
				return m.author.id == user.id
		await ctx.message.delete()
		m = await self.how_to_purge(ctx, amount, check=check)
		await ctx.send(f"Deleted {m} messages.", delete_after=5)

	@staticmethod
	async def how_to_purge(ctx, amount: int, check=None):
		try:
			p = await ctx.channel.purge(limit=amount, check=check)
			return len(p)
		except discord.Forbidden:
			try:
				p = await ctx.channel.purge(limit=amount, check=check, bulk=False)
				return len(p)
			except:
				d = 0
				async for message in ctx.channel.history(limit=amount):
					if check is not None:
						if check:
							await message.delete()
							d += 1
				return d

	@purge.command(name='me', alises=['self'])
	@commands.check(can_purge_self)
	@commands.bot_has_permissions(manage_messages=True)
	async def _me(self, ctx, amount: int = 100):
		"""Clean only the bot's messages"""

		def check(m):
			return m.author == self.bot.user

		await ctx.message.delete()
		x = await self.how_to_purge(ctx, amount, check=check)
		await ctx.send(f'deleted {x} of my messages!', delete_after=10)

	@purge.command()
	@checks.admin_or_permissions(manage_messages=True)
	@commands.bot_has_permissions(manage_messages=True)
	async def bots(self, ctx, amount: int = 100):
		"""Purge messages by bots"""

		def check(m):
			return m.author.bot

		await ctx.message.delete()
		p = await ctx.channel.purge(limit=amount, check=check)
		await ctx.send(f'purged {len(p)} messages by bots!', delete_after=10)

	@purge.command()
	@checks.admin_or_permissions(manage_messages=True)
	@commands.bot_has_permissions(manage_messages=True)
	async def user(self, ctx, user: discord.User, amount: int = 100):
		"""Purge messages from a user"""

		def check(m):
			return m.author == user if user is not None else ctx.author

		X = await self.how_to_purge(ctx, amount, check=check)
		await ctx.send(f'deleted {X} messages by {user.name}', delete_after=10)

	@purge.group()
	@checks.admin_or_permissions(manage_messages=True)
	@commands.bot_has_permissions(manage_messages=True)
	async def text(self, ctx, amount: int, *, text: str):
		"""scan <amount> messages and check if [text] is in them."""
		def check(m):
			return text in m.content
		x = await self.how_to_purge(ctx, amount, check=check)
		await ctx.send(f"deleted {x} messages.", delete_after=10)

	@text.command()
	@checks.admin_or_permissions(manage_messages=True)
	@commands.bot_has_permissions(manage_messages=True)
	async def regex(self, ctx, amount: int, pattern: str):
		"""check on a regex. advanced."""
		def check(m):
			return re.search(pattern.lower(), m.content.lower())

def setup(bot):
	bot.add_cog(Mod(bot))
