import discord
import asyncio
import logging as logger
import typing
import json as _json

from discord.ext import commands, tasks
from cogs.config import json_mngr as json

temp = 'List Autoroles. to view subcommands, invoke help.'


class AutoRole(commands.Cog):
	"""Autorole Management"""

	def __init__(self, bot):
		self.bot = bot
		self.data = {}  # not read yet
		self.data_updater.start()

	def cog_unload(self):
		self.data_updater.stop()

	@tasks.loop(minutes=10)
	async def data_updater(self):
		t = json.read('./data/autorole.json')
		self.data = t
		logger.info("cogs.autorole: successfully updated `self.json`")

	@commands.group(name="autorole", aliases=['ar', 'arsetup', 'autoroles'], case_insensitive=True, brief=temp, invoke_without_command=True)
	async def autorole(self, ctx):
		"""list autoroles."""
		# await ctx.send(self.data)
		if str(ctx.guild.id) not in self.data.keys():
			if self.data == {}:
				return await ctx.send("Error retrieving data. Please try again in a minute.")
			return await ctx.send("This guild has no auto-roles!")
		else:
			roles = self.data[str(ctx.guild.id)].keys()
			roleobjs = []
			for role in roles:
				_role = ctx.guild.get_role(int(role))
				if _role is None:
					continue
				roleobjs.append((_role, self.data[str(ctx.guild.id)][str(_role.id)]))  # <role>, {{...}}
			e = discord.Embed(title="Autoroles and their configs:", description="", color=discord.Color.gold())
			for roleo, config in roleobjs:
				e.description += f'{roleo.mention}:\nbots only: {config["botmode"]}\ndelay: {config["delay"]}s\n**---**\n'
			await ctx.send(embed=e)

	@autorole.command(name="all", aliases=['debug'])
	@commands.is_owner()
	async def autorole_debug(self, ctx, public: typing.Optional[bool], *, guild_id: int = None):
		"""Debug autoroles (data). provide a guild id to get their information."""
		if public is None:
			public = True
		guild_id = str(guild_id)
		data = str(self.data)
		pages = commands.Paginator(prefix='CACHED CONTENT:\n```json')
		if guild_id:
			if guild_id in self.data:
				data = str(self.data[guild_id])
		lines = data.splitlines(keepends=False)
		for line in lines:
			pages.add_line(line)
		for page in pages.pages:
			if public:
				await ctx.send(page, delete_after=120)
			else:
				await ctx.author.send(page)
			await asyncio.sleep(1)

		real_data = json.read('./data/autorole.json')
		paginator = commands.Paginator(prefix="FILE CONTENT:\n```json")
		for line in str(real_data).splitlines(keepends=False):
			paginator.add_line(line)
		for page in paginator.pages:
			if public:
				await ctx.send(page, delete_after=120)
			else:
				await ctx.author.send(page)
			await asyncio.sleep(1)
		await ctx.message.add_reaction('success:522078924432343040')

	@autorole.command(name="info", aliases=["about"])
	async def autorole_info(self, ctx, role: discord.Role):
		"""get information on a role"""
		if str(ctx.guild.id) not in self.data:
			if self.data == {}:
				return await ctx.send("Error retrieving data. Please try again in a minute.")
			return await ctx.send("This guild has no auto-roles!")
		else:
			if str(role.id) in self.data[str(ctx.guild.id)].keys():
				__data = self.data[str(ctx.guild.id)][str(role.id)]
				delay = __data['delay']
				botmode = __data['botmode']
				f = f"""{role.id}:
				delay: {delay}s
				bot mode: {botmode}"""
				await ctx.send(f)
			else:
				await ctx.send("that role isn't an autorole!")

	@autorole.command(name="add", aliases=['create'])
	@commands.has_permissions(manage_roles=True)
	@commands.cooldown(1, 1, commands.BucketType.default)
	async def autorole_add(self, ctx, role: discord.Role, delay: typing.Optional[int], bots_only: bool = False):
		"""add an autorole to the list of autoroles."""
		delay = delay if delay else 0
		if str(ctx.guild.id) not in self.data.keys():
			self.data[str(ctx.guild.id)] = {}
		if str(role.id) in self.data[str(ctx.guild.id)]:
			return await ctx.send("that role is already listed!")
		if role >= ctx.guild.me.top_role:
			return await ctx.send("That role is too high! please give me a role higher then that role.")
		self.data[str(ctx.guild.id)][str(role.id)] = {"delay": delay, "botmode": bots_only}
		with open('./data/autorole.json', 'w') as _file:
			_json.dump(self.data, _file)
		await ctx.send(f"Added {role.id} to the autoroles. it may take up to 10 seconds to apply.")

	@autorole.command(name="remove", aliases=['delete'])
	@commands.has_permissions(manage_roles=True)
	@commands.cooldown(1, 1, commands.BucketType.default)
	async def autorole_remove(self, ctx, role: discord.Role):
		"""Remove an autorole from the list"""
		if str(ctx.guild.id) not in self.data:
			if self.data == {}:
				return await ctx.send("Error retrieving data. Please try again in a minute.")
			return await ctx.send("This guild has no auto-roles!")
		if str(role.id) not in self.data[str(ctx.guild.id)].keys():
			return await ctx.send(f"That role is not in your autoroles!\nrun `{ctx.prefix}autorole` to get a list.")
		del self.data[str(ctx.guild.id)][str(role.id)]
		json.handle_modify('./data/autorole.json', newdata=self.data, indent=1, backup=True)
		await ctx.send(f"Removed {role.id} from autoroles. it may take up to 10 seconds to apply.")

	async def add_role(self, guild, member, _role):
		_role = guild.get_role(int(_role))
		if _role is None:
			return
		roleconfig = self.data[str(guild.id)][str(_role.id)]
		await asyncio.sleep(roleconfig["delay"])

		if roleconfig["botmode"]:
			if member.bot:
				await member.add_roles(_role, reason="AutoRole")
			else:
				return
		else:  # botmode: False
			if member.bot:
				return
			if _role >= guild.me.top_role:
				if guild.system_channel:
					try:
						w = '\u200B'
						await guild.system_channel.send(f"I was unable to give "
														f"**{member.display_name.replace('@', f'@{w}')}** "
														f"autorole with the ID {_role.id} because the role is too "
														f"high.")
					except (TypeError, AttributeError, discord.Forbidden, discord.NotFound, Exception):
						pass
				else:
					return
			try:
				await member.add_roles(_role, reason="AutoRole")
			except (discord.Forbidden, Exception):
				if guild.system_channel:
					try:
						w = '\u200B'
						await guild.system_channel.send(f"I was unable to give "
														f"**{member.display_name.replace('@', f'@{w}')}** "
														f"autorole with the ID {_role.id}.")
					except (TypeError, AttributeError, discord.Forbidden, discord.NotFound, Exception):
						pass
				else:
					return

	@commands.Cog.listener(name="on_member_join")
	async def add_the_autoroles(self, member: discord.Member):
		"""add the autoroles"""
		guild = member.guild
		if str(guild.id) not in self.data.keys():
			return
		for role in self.data[str(guild.id)].keys():
			self.bot.loop.run_in_executor(None, await self.add_role(guild, member, role))  # speed up the addition


def setup(bot):
	bot.add_cog(AutoRole(bot))