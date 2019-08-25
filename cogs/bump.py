import discord, random, asyncio, aiohttp, datetime, json
from discord.ext import commands
from utils import checks

class Bump(commands.Cog):

	def __init__(self, bot):
		self.bot = bot
		self.dtf = "%I:%M %p @ %d/%m/%Y %Z"
		self.success = 'success:522078924432343040'
		self.loading = 'a:loading20:553253741311295498'
		self.error = 'fail:522076877075251201'
		self.colors = [discord.Color.red(), discord.Color.orange(), discord.Color.gold(), discord.Color.green(),
					   discord.Color.blue(), discord.Color.purple(), discord.Color.blurple()]
		self.on_cooldown = []
		self.autobumping = {}
	@staticmethod
	def get_rank(ctx):
		guild = discord.utils.get(ctx.bot.guilds, id=486910899756728320)
		member = discord.utils.get(guild.members, id=ctx.author.id)
		for x in guild.roles:
			if x.name == 'Donator':
				return 'Donator'
			elif x.name == 'Voted':
				if x in member.roles:
					return 'Voted'
			else:
				continue
		else:
			return 'Member'
	async def cooldown(self, ctx: commands.Context, time:int):
		self.on_cooldown.append(ctx.guild.id)
		await asyncio.sleep(time)
		self.on_cooldown.remove(ctx.guild.id)
	@staticmethod
	async def findchannel(ctx):
		#with open('./data/config.json', 'r') as dataa:
		#	data = json.load(dataa)
		#	if str(ctx.guild.id) in data['bumpchannels']:
		#		try:
		#			channel = await ctx.bot.fetch_channel(data['bumpchannels'][str(ctx.guild.id)])
		#			return channel
		#		except (discord.NotFound, KeyError):
		#			pass
		#	else:
		#		pass
		for x in ctx.guild.text_channels:
			if x.name == 'bump' or x.name =='ylb-bump':
				return x
			elif x.topic is not None and x.topic.startswith('yb'):
				return x
		else:
			return None

	async def bumpmethod(self, embed):
		"""loop through guilds and bump"""
		fmt = ""
		for g in self.bot.guilds:
			# with open('./data/config.json', 'r') as dataa:
			#	data = json.load(dataa)
			#	if str(g.id) in data['bumpchannels']:
			#		try:
			#			channel = await self.bot.fetch_channel(data['bumpchannels'][str(g.id)])
			#			await channel.send(embed=embed)
			#			continue
			#		except (discord.NotFound, KeyError):
			#			pass
			#	else:
			#		pass
			for c in g.text_channels:
				if c.name == 'bump' or c.name == 'ylb-bump':
					try:
						await c.send(embed=embed)
						fmt += f"<:{self.success}> `{g.name}`\n"
						continue
					except:
						fmt += f"<:{self.error}> `{g.name}`\n"
		return fmt

	async def get_cooldown(self, ctx):
		rank = self.get_rank(ctx)
		if rank == 'Member':
			cd = 600
		elif rank == 'Voted':
			cd = 300
		elif rank == 'Donator':
			cd = 120
		else:
			cd = 600
		return cd
	@commands.command(aliases=['b', 'send'])
	@commands.cooldown(1, 5, commands.BucketType.guild)
	@commands.bot_has_permissions(manage_guild=True, manage_messages=True, embed_links=True, read_message_history=True, external_emojis=True, add_reactions=True, manage_channels=True)
	async def bump(self, ctx):
		"""bUmp your server to others!"""
		if str(ctx.guild.id) in self.autobumping:
			return await ctx.send('this server is currently autobumping!')
		if ctx.guild.id in self.on_cooldown:
			E=discord.Embed(
				title="Cooldowns:",
				description="Regular: 10 minutes\nVoted: 5 minutes (must be in support server)\n" \
							"Donated: 2 minutes (must be in support server)",
				color=discord.Color.gold()
			)
			return await ctx.send('Sorry, but you are on cooldown!', embed=E, delete_after=15)
		m = ctx.message
		rank = self.get_rank(ctx)
		if rank == 'Member':
			cd = 600
		elif rank == 'Voted':
			cd = 300
		elif rank == 'Donator':
			cd = 120
		else:
			cd = 600
		await m.add_reaction(self.loading)
		chan = await self.findchannel(ctx)
		if chan is None:
			await m.clear_reactions()
			await m.add_reaction(self.error)
			return await ctx.send("I couldn't find a channel with the name `bump` or a channel topic that starts with"
								  " `yb`!\n*psst:  want a custom one? do `y!config bumphannel #<channel>`!*")
		else:
			if chan.topic.startswith('yb'):
				topic = chan.topic.strip('yb ').strip('yb')
			else:
				topic = chan.topic
			if len(topic) < 25:
				await m.clear_reactions()
				await m.add_reaction(self.error)
				await ctx.send(f"Your bump message must be longer then 25 characters. it is currently {len(topic)} long")
				return self.bot.get_command(ctx.command.name).reset_cooldown(ctx)
			x = None
			if len(ctx.guild.emojis) > 1:
				x = random.choice(ctx.guild.emojis)
			mb = ('\U0001f4d8' if not x else x)
			for i in await ctx.guild.invites():
				if i.max_uses == 0 and i.max_age == 0:
					invite = i.url
					break
			else:
				i = await ctx.channel.create_invite()
				invite = i.url
			e = discord.Embed(title=ctx.guild.name, description=topic, color=discord.Color.blue(), url=invite, timestamp=datetime.datetime.utcnow())
			e.add_field(name="Statistics:", value=f"Members: {len(ctx.guild.members)} \U000026f9\nChannels: "
			f"{len(ctx.guild.text_channels)}\U0001f4ac\nEmojis: {len(ctx.guild.emojis)} "
			f"{mb}\n"
			f"Owner: {ctx.guild.owner}\U0001f451\nId: {ctx.guild.id}\U0001f194"
			f"\nCreated on:"
			f" {ctx.guild.created_at.strftime(self.dtf)} \U0001f552\n"
			f"Invite: **{invite}** \N{CHAINS}")
			e.set_thumbnail(url=ctx.guild.icon_url)
			e.set_footer(text=f"bumped by: {ctx.author.name}")
			bump = await self.bumpmethod(e)
			await m.clear_reactions()
			await m.add_reaction(self.success)
			await ctx.send(bump)
			await self.cooldown(ctx, cd)


	@commands.command()
	@checks.co_owner()
	async def getrank(self, ctx, user: discord.User = None):
		ctx.author = ctx.author if user is None else user
		return await ctx.send(self.get_rank(ctx))

	@commands.group(invoke_without_command=True)
	@commands.cooldown(1, 10800, commands.BucketType.guild)
	@commands.bot_has_permissions(manage_guild=True, manage_messages=True, embed_links=True, read_message_history=True, external_emojis=True, add_reactions=True, manage_channels=True)
	async def autobump(self, ctx):
		"""autobump your server!

		will bump every 10 minutes until reboot.
		note that you will not be told the regular output of bump."""
		channel = await self.findchannel(ctx)
		if channel is None:
			ctx.command.reset_cooldown(ctx)
			return await ctx.send("No channel named `ylb-bump` or `bump` found!")
		if channel.topic is None:
			ctx.command.reset_cooldown(ctx)
			return await ctx.send("No channel named `ylb-bump` or `bump` with a topic found!\n*your channel topic is"
								  " your bump message.")
		if len(channel.topic) <= 25:
			return await ctx.send(f"Your bump topic is too short! it must be greater then 25 characters long!")
		# now that it is satisfied
		x = await ctx.send("checking...")
		rank = self.get_rank(ctx)
		if rank.lower() != 'donator':
			return await x.edit(content="Only premium users can do this!")
		for gi in self.autobumping:
			if self.autobumping[gi] == ctx.author.id:
				b = discord.utils.get(self.bot.guilds, id=int(gi))
				if ctx.author not in b.members:
					await x.edit(content=f"Cancelling autobump in {b.name} because you aren't there...")
					del self.autobumping[str(b.id)]
					await x.edit(content=f"cancelled autobumping in {b.name}! initiating here...")
					break
				ctx.command.reset_cooldown(ctx)
				return await x.edit(content="You are already autobumping a server! go to {} and type `"
											"y!autobump cancel` to cancel autobumping.".format(
					discord.utils.get(self.bot.guilds, id=int(gi)).name
				))
		await x.delete()
		await ctx.send("Autobumping until reboot or interrupeted.")
		self.autobumping[str(ctx.guild.id)] = ctx.author.id
		try:
			while str(ctx.guild.id) in list(self.autobumping):
				mb = ('\U0001f4d8' if len(ctx.guild.emojis) <= 1 else random.choice(ctx.guild.emojis))
				for i in await ctx.guild.invites():
					if i.max_uses == 0 and i.max_age == 0:
						invite = i.url
						break
				else:
					i = await ctx.channel.create_invite()
					invite = i.url
				e = discord.Embed(title=ctx.guild.name, description=channel.topic, color=discord.Color.blue(), url=invite, timestamp = datetime.datetime.utcnow())
				e.add_field(name="Statistics:", value=f"Members: {len(ctx.guild.members)} \U000026f9\nChannels: "
				f"{len(ctx.guild.text_channels)}\U0001f4ac\nEmojis: {len(ctx.guild.emojis)} "
				f"{mb}\n"
				f"Owner: {ctx.guild.owner}\U0001f451\nId: {ctx.guild.id}\U0001f194\n"
				f"Invite: **{invite}** \N{CHAINS}")
				e.set_thumbnail(url=ctx.guild.icon_url)
				e.set_footer(text=f"autobumped by: {ctx.author.name}")
				fmt = ""
				await self.bumpmethod(e)
				await asyncio.sleep(600)
			await ctx.send("Autobump ended by extental cause")
		except discord.ext.commands.errors.CommandInvokeError:
			await ctx.send("```diff\nCONNECTION FAILED - AUTOBUMP CANCELLED\n```")

	@autobump.command(name="cancel")
	async def autobump_cancel(self, ctx):
		"""Cancel autobumping"""
		if str(ctx.guild.id) in self.autobumping:
			if ctx.author.id != self.autobumping[str(ctx.guild.id)] and ctx.author.id != ctx.guild.owner.id:
				return await ctx.send(f"You aren't autobumping! please contact this ID: "
									  f"{self.autobumping[str(ctx.guild.id)]}")
			del self.autobumping[str(ctx.guild.id)]
			await ctx.send("Stopped autobumping.")
			self.bot.get_command('autobump').reset_cooldown(ctx)
		else:
			await ctx.send("This server isn't being autobumped!")
		if ctx.author.id == self.bot.owner_id:
			await ctx.send(self.autobumping)



def setup(bot):
	bot.add_cog(Bump(bot))
