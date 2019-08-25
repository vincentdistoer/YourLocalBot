import discord, asyncio, typing, datetime
from discord.ext import commands
from utils import checks
from typing import Union
class guild_checks:
	@staticmethod
	def can_approve():
		def predi(ctx):
			role = discord.utils.get(discord.utils.get(ctx.bot.guilds, id=579727903101550602).roles,
									 name='Approval Team')
			return ctx.author in role.members or ctx.author == ctx.guild.owner
		return commands.check(predi)
	@staticmethod
	def is_guild():
		def p(ctx):
			return ctx.guild.id == 579727903101550602
		return commands.check(p)
class DragBoatz(commands.Cog):
	"""the official DragBoatz guild cog!"""
	def __init__(self, bot):
		self.bot = bot


	@commands.command()
	@guild_checks.is_guild()
	@guild_checks.can_approve()
	async def claim(self, ctx, message_id: discord.Message):
		"""Claim a bot to say that you are testing it! `Bot` is the submitted bot's message id from #submitted."""
		c = discord.utils.get(ctx.guild.channels, name="submitted")
		try:
			m = await c.fetch_message(message_id)
		except discord.NotFound:
			return await ctx.send('⛔️ Embed not found. please ensure it is in #submitted')
		b = m.embeds[0]
		if b.author:
			return await ctx.send(f'⛔️ {b.author.name} is testing this bot!')
		b.url = None
		b.set_author(name=ctx.author.name)
		await m.edit(embed=b)
		await ctx.send('✅ now testing that bot.')
	@commands.command()
	@guild_checks.is_guild()
	async def submit(self, ctx):
		"""
		guides you through the bot submission progression! INTERACTIVELY!
		"""
		if ctx.channel.id not in [580062771157270528, 580063088792043521, 580063123009044512]:
			return await ctx.send('please use this command in either #commands-1, #commands-2 or #bot-hell.')
		def check(m):
			return m.channel == ctx.channel and m.author == ctx.author
		async def wait():
			try:
				ret = await self.bot.wait_for('message', check=check, timeout=120)
			except asyncio.TimeoutError:
				return await message.edit(content="Timed out.", embed=None)
			return ret  # will return so long as it doesnt time out
		message = await ctx.send('Preparing...')
		e = discord.Embed()
		await message.edit(embed=e)
		await asyncio.sleep(0.25)
		# getting url & user ID
		await message.edit(content=f"Hello {ctx.author.name}! welcome to the bot submission process!\n"
		f"In this short command, i will guide you through the submission process, displaying"
		f" the embed that will be send for review below! You can say `cancel` at any time"
		f" to cancel the submission process.\n\nFirst off, whats your bot's ID?")
		try:
			bot_id_raw = await self.bot.wait_for('message', check=check, timeout=120)
			try:
				bot_id = bot_id_raw.content
				bot_id = int(bot_id)
				invite_url = discord.utils.oauth_url(str(bot_id), guild=ctx.guild)
				bot = await self.bot.fetch_user(bot_id)
				if not bot.bot:
					return await message.edit(content='that\'s not a bot!')
				elif bot in ctx.guild.members:
					return await message.edit(content="That bot is either being tested or is already approved!", embed=None)
				e.title=bot.name
				e.url = invite_url
				e.set_thumbnail(url=str(bot.avatar_url).replace('webp', 'png'))
				await asyncio.sleep(1)
				await bot_id_raw.delete()
			except:
				return await message.edit(embed=None, content="Sorry, but you didn't pass a valid user ID!")
			await message.edit(embed=e)
		except asyncio.TimeoutError:
			return await message.edit(content="Timed out.", embed=None)
		# getting description
		await message.edit(content="Great! now, whats your bots long description? please be as descriptive as possible."
								   "\nMax chars: 256\nMin chars: 25")
		try:
			desc = await self.bot.wait_for('message', check=check, timeout=120)
			if len(desc.content) < 25:
				return await message.edit(content="Too short.")
			e.add_field(name='Description:', value=desc.content[:256], inline=False)
			e.color = ctx.author.color
			await message.edit(embed=e)
			await desc.delete(delay=1)
		except asyncio.TimeoutError:
			return await message.edit(content="Timed out.", embed=None)
		await message.edit(content="what tags? (Example: mod, games)\ntags are separated via `,`. Max tags: 6", embed=e)
		try:
			tags = await wait()
			_tags = tags
			tags = tags.content.split(',')
			if len(tags) > 6:
				tags = tags[:6]
			addtags=True
			await _tags.delete(delay=1)
		except asyncio.TimeoutError:
			addtags = False
		await message.edit(content="Great! now, whats your bot's short description?\nMax chars: 100")
		sd = await wait()
		if len(sd.content) < 40:
			return await message.edit(content="too short! 40+")
		e.description = sd.content[:100]
		await sd.delete(delay=1)
		await message.edit(embed=e)
		await message.edit(content="ok, and what is it's prefix(es)?")
		prefixes_raw = await wait()
		prefixes = prefixes_raw.content
		await prefixes_raw.delete(delay=1)
		await message.edit(content="ok, and do you have a support server? if not, just reply `no`.")
		sg_raw = await wait()
		if sg_raw.content.lower().startswith('n') or not sg_raw.content.lower().startswith('http'):
			sg = 'None'
		else:
			sg = sg_raw.content
		if addtags:
			e.add_field(name="tags:", value=', '.join(tags), inline=False)
		e.add_field(name="Misc:", value=f"Prefix(es): {prefixes}\nSupport Guild: {sg}\nOwner: {ctx.author.mention}",
					inline=False)
		t = await ctx.send(content="and that's it! just to confirm, is this what you believe the embed should say? [y/n]")
		await message.edit(embed=e, content=None)
		await sg_raw.delete(delay=1)
		try:
			c = await self.bot.wait_for('message', check=check, timeout=120)
			c = c.content
			if c.lower().startswith('y'):
				channel = discord.utils.get(ctx.guild.channels, name='submitted')
				role = discord.utils.get(ctx.guild.roles, name='Approval Team')
				await channel.send(role.mention + ' ' + str(bot.id), embed=e)
				remaining = await channel.history(limit=9999).flatten()
				await message.edit(content=f'all done. bots in queue: `{len(remaining)}`',embed=None)
				await c.delete(delay=1)
				await t.delete(delay=1)
			else:
				return await message.edit(content="cancelled")
		except asyncio.TimeoutError:
			return await message.edit(content="Timed out.", embed=None)

	@commands.command(aliases=['approve', 'allow'])
	@guild_checks.is_guild()
	@guild_checks.can_approve()
	async def accept(self, ctx, bot: discord.Member, owner: discord.Member, *, notes: str = None):
		"""Accept a bot!"""
		def check(m):
			return m.author == ctx.author and m.channel == ctx.channel
		sent = discord.utils.get(ctx.guild.channels, name="submitted")
		log = discord.utils.get(ctx.guild.channels, name="bot-logs")
		async for message in sent.history(limit=9999):
			m = message.content.lower()
			if message.author == self.bot.user:
				if m.endswith(str(bot.id)):
					e = message.embeds[0]
					ask = await ctx.send('Is this the correct embed?', embed=e)
					ask_event = await self.bot.wait_for('message', check=check)
					if ask_event.content.lower().startswith('y'):
						if not e.author:
							return await ask.edit(embed=None, content=f"This bot has not been claimed for testing. Use `y!claim {message.id}` then try again!")
						elif e.author.name != ctx.author.name:
							return await ask.edit(content=f"You aren't reviewing this bot! {e.author.name} must approve/deny!")
						e.url = f'https://discordapp.com/api/oauth2/authorize?client_id={str(bot.id)}&scope=bot'
						e.set_author(name=bot.id)
						embed = e
						message = message
						break
					else:
						continue
		else:
			return await ctx.send('bot not found in #submitted; has it been submitted?')
		if notes is not None:
			embed.set_footer(text=f"Notes: {notes}")
		await bot.remove_roles(discord.utils.get(ctx.guild.roles, id=579789489405165579), reason="bot approval")
		await bot.add_roles(discord.utils.get(ctx.guild.roles, id=579747959365697585), reason="bot approval - pt.2")
		await owner.add_roles(discord.utils.get(ctx.guild.roles, id=579789322019012608), reason="bot approval - pt.3")
		await log.send(f'{bot.mention} by {owner.mention} was accepted by {ctx.author}')
		fab = discord.utils.get(ctx.guild.text_channels, name="find-a-bot")
		await fab.send(embed=e)
		await message.delete()

	@commands.command(aliases=['reject', 'decline'])
	@guild_checks.is_guild()
	@guild_checks.can_approve()
	async def deny(self, ctx, bot: Union[discord.Member, discord.User], owner: discord.Member, *, reason: commands.clean_content):
		"""Deny a bot."""
		def check(m):
			return m.author == ctx.author and m.channel == ctx.channel
		sent = discord.utils.get(ctx.guild.channels, name="submitted")
		log = discord.utils.get(ctx.guild.channels, name="bot-logs")
		async for message in sent.history(limit=9999):
			m = message.content.lower()
			if message.author == self.bot.user:
				if m.endswith(str(bot.id)):
					e = message.embeds[0]
					ask = await ctx.send('Is this the correct embed?', embed=e)
					ask_event = await self.bot.wait_for('message', check=check)
					if ask_event.content.lower().startswith('y'):
						if not e.author:
							return await ask.edit(embed=None, content=f"This bot has not been claimed for testing. Use `y!claim {message.id}` then try again!")
						elif e.author.name != ctx.author.name:
							return await ask.edit(content=f"You aren't reviewing this bot! {e.author.name} must approve/deny!")

						embed = e
						message = message
					else:
						continue
		await log.send(f'{bot.mention} by {owner.mention} was declined by {ctx.author} for: {reason}.')
		await message.delete()
		if isinstance(bot, discord.User):
			return
		await bot.kick(reason='Declined')
	@staticmethod
	def questions():
		return ["Name and age-range", "How long have you been a member of the server?",
				"A bot responds to \"spill\" which is not listed as a prefix. WDYD?",
				"Someone is using a bot to spam. WDYD?", "A bot has a  say command. You go to approval-private And the bot pings @here. WDYD?",
				]
	async def get_answer(self, ctx):
		def c(m):
			return m.author == ctx.author and m.guild is None
		try:
			to_ret = await self.bot.wait_for('message', check=c, timeout=180)
			return to_ret
		except asyncio.TimeoutError:
			return None

	@commands.command(disabled=True)
	@guild_checks.is_guild()
	@commands.cooldown(1, 3600, commands.BucketType.user)
	async def apply(self, ctx):
		"""Apply for a staff rank!"""
		try:
			message = await ctx.author.send('loading')
		except:
			return await ctx.send('I need to DM you to apply for approval Team!')
		e = discord.Embed(title="Approval Team application:", description="apply truthfully.", color=discord.Color.dark_blue())

		e.set_author(icon_url=str(ctx.author.avatar_url).replace('.webp', '.png'), name=ctx.author.name)
		for n, q in enumerate(self.questions(), start=1):
			e.add_field(name=f"{n}: {q}", value="*your response will be added here upon reply", inline=False)
			await message.edit(content=None, embed=e)
			answer = await self.get_answer(ctx)
			if answer is None:
				return await message.edit(content="Timed out.")
			e.remove_field(n-1)
			e.add_field(name=f"{n}: {q}", value=answer.content)
		await message.edit(content="are you sure you want to submit this? **[yes/no]**")
		answer = await self.get_answer(ctx)
		if answer is None:
			return await message.edit(content="I guess not, then.")
		if answer.content.lower().startswith('n'):
			return await message.edit(content="ok then. Try again later.")
		elif answer.content.lower().startswith('y'):
			await message.edit(content="sending...", embed=None)
		else:
			return await message.edit(content="ok then. Cancelled.")
		channel = discord.utils.get(ctx.guild.text_channels, name="logs")
		await channel.send(embed=e)
		await message.edit(content="Sent!")
	@commands.command()
	@guild_checks.is_guild()
	@guild_checks.can_approve()
	async def delete(self, ctx, bot: discord.Member, owner: discord.Member, *, reason: commands.clean_content):
		"""Delete a bot from the bot list"""
		die = await ctx.send("Finding...")
		async with ctx.channel.typing():
			fab = discord.utils.get(ctx.guild.text_channels, name="find-a-bot")
			log = discord.utils.get(ctx.guild.channels, name="bot-logs")
			fab_msgs = await fab.history(limit=9999999).flatten()
			for message in fab_msgs:
				if len(message.embeds) > 0:
					if owner.mention in [x.value for x in message.embeds[0].fields]:
						await die.edit(content="Is this the correct bot? [y/n]", embed=message.embeds[0])
						x = await self.bot.wait_for('message', check=lambda a: (a.author == ctx.author and a.channel == ctx.channel))
						if not x.content.lower().startswith('y'):
							continue
						await message.edit(content="Mk, deleting bot now.", embed=None)
						break
			else:
				await die.edit(content="\U0000274e - unable to find any matching embeds in find-a-bot; manual.")
				await asyncio.sleep(5)
			await bot.kick(reason=f"deleted by {ctx.author} for: {reason}")
			try:
				await owner.send(f"Sorry, but your bot {bot.mention} was deleted from {ctx.guild.name} for: {reason}")
			except discord.Forbidden:
				await discord.utils.get(ctx.guild.channels, name="general").send(f"Sorry, but your bot {bot.mention} was deleted for: {reason}")
		await log.send(f"{bot.name} by {owner.name} was deleted.")
		await self.bot.get_channel(579749829421563944).send(f'{bot.name} by {owner} was deleted by {ctx.author} for:\n{reason}')
		await die.edit(content=f"\U00002611 deleted {bot}")

	@commands.command(name="responsetest", aliases=["botresp", "rt"])
	@guild_checks.is_guild()
	@guild_checks.can_approve()
	async def response_test(self, ctx, prefix: str, *, command: str = ""):
		"""Make the bot say stuff to see if a bot responds to bot text"""
		await ctx.send(prefix + command)
		await ctx.message.delete()

	@commands.command()
	@guild_checks.is_guild()
	@guild_checks.can_approve()
	async def notify(self, ctx, owner: discord.Member, bot: discord.Member, *, stuff):
		"""DM the owner of a bot about something."""
		stuff = f"*{ctx.author.name} is contacting you about {bot.name}:*\n\"{stuff}\"\nif you feel this method of contact" \
			" has been abused, please contact staff management or an owner."
		try:
			await owner.send(stuff)
			await ctx.message.add_reaction('\U00002611')
		except discord.Forbidden:
			await ctx.send("403: forbidden.")
	@commands.Cog.listener()
	async def on_member_join(self, member):
		if member.guild.id == 579727903101550602:
			if member.bot:
				role = discord.utils.get(member.guild.roles, id=579789489405165579)
				await member.add_roles(role, reason='botlist autorole')
			else:
				role = discord.utils.get(member.guild.roles, name='Users')
				await member.add_roles(role, reason='Member  autorole')

def setup(bot):
	bot.add_cog(DragBoatz(bot))
