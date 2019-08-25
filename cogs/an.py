import asyncio
import datetime
import os
import random
import time
import traceback
from random import randint

import aiohttp
import discord
from discord import AsyncWebhookAdapter, Webhook, WebhookAdapter
from discord.ext import commands

from utils.page import pagify


class ErrorHandler(commands.Cog):
	"""handles errors, if i can logic."""
	def __init__(self, bot):
		self.bot = bot
		self.dtf = "%I:%M %p @ %d/%m/%Y %Z"

	async def send_tb(self, ctx, channelobj: discord.TextChannel, *, cid: int, tb: str = None, pages: list = None):
		if tb is None and pages is None:
			raise ValueError("tb or pages must be provided")
		index = await channelobj.send(f"**Case {cid}:**")
		msgs = []
		for page in pages:
			x = await channelobj.send(page)
			msgs.append(x.jump_url)
		y = f"Author: {ctx.author} | `{ctx.author.id}`\nCommand: {ctx.command.qualified_name} |"\
			f" {str(ctx.command.cog.qualified_name)}\nGuild: {ctx.guild if ctx.guild else 'DM'} | `" \
			f"{ctx.guild.id if ctx.guild else ctx.channel.id}`\nMy Permissions: " \
			f"{ctx.channel.permissions_for(ctx.me).value if ctx.guild else 'DM'}\n" \
			f"Their Permissions: {ctx.channel.permissions_for(ctx.author).value if ctx.guild else 'DM'}"

		x = await channelobj.send(y)
		msgs.append(x.jump_url)
		ws = '\n'
		await index.edit(content=f"**Case {index.id}:**\n\n*index: {ws.join(msgs)}*")
		await index.channel.send('```\n```')
		return index

	@commands.Cog.listener()
	async def on_command_error(self, ctx, error):
		NH = self.bot.get_command('help')
		if isinstance(error, commands.CommandNotFound):
			return

		elif ctx.command.name == 'help':
			if isinstance(error, commands.CommandInvokeError):
				await ctx.send(error)
			else:
				await ctx.send(f"Unhandled `help` error (`{str(error)}`)")
				raise error
		elif isinstance(error, commands.DisabledCommand):
			await ctx.send('Sorry, but this command is temporarily disabled. This is most likely because a bug hs been'
						   ' found, or the command is in the process of being updated.')
		elif isinstance(error, discord.ext.commands.errors.CommandOnCooldown):
			seconds = round(error.retry_after)
			minutes = 0
			while seconds >= 60:
				seconds -= 60
				minutes += 1
			await ctx.send(f"This command is on cooldown!\nyou can rerun in {minutes} mins and {seconds} seconds.")
		elif isinstance(error, commands.BotMissingPermissions):
			if len(error.missing_perms) > 1:
				fm = ', '.join(error.missing_perms)
			else:
				fm = f"{error.missing_perms}"
			e = discord.Embed(
				title="Im missing permissions!",
				description=f"{ctx.command.name} needs `{fm}`",
				color=discord.Color.red()
			)
			await ctx.send(embed=e, delete_after=10)
		elif isinstance(error, commands.CheckFailure):
			if ctx.author.id in list(self.bot.locked_out):
				e = discord.Embed(title="You lack permission to use this bot!")
				e.description="You are currently blacklisted from using the bot. If you believe this is in error, contact a dev." \
					f"**Reason:** {self.bot.locked_out[ctx.author.id]}"
				e.color=discord.Color.red()
			elif self.bot.global_lockout:
				e = discord.Embed(title="The bot is currently on a global lockout. Try again later.")
				e.color=discord.Color.red()
			else:
				e = discord.Embed(title="You lack permissions for this command!",
								  color=discord.Color.red())
				try:
					e.description="You need: `" + '`, `'.join(error.missing_perms) + "`."
				except:
					pass
			return await ctx.send(embed=e, delete_after=60)
		elif isinstance(error, discord.ext.commands.errors.MissingRequiredArgument):
			await ctx.send("Missing argument! please use the below guide")
			await ctx.invoke(NH, command=ctx.command.qualified_name)
		elif isinstance(error, discord.ext.commands.errors.BadArgument):
			await ctx.send(f"Invalid argument\n({str(error)})")
			await ctx.invoke(NH, command=ctx.command.qualified_name)
		else:
			exception_channel = self.bot.get_channel(613073501372416000)
			try:
				raise error
			except:
				tb = traceback.format_exc()
			paginator = commands.Paginator(prefix="```py")
			lines = tb.splitlines(keepends=False)
			for line in lines:
				paginator.add_line(line[:2000])
			case_id = await self.send_tb(ctx, exception_channel, cid=ctx.message.id, pages=paginator.pages)
			case_id = case_id.id

			url = 'https://invite.gg/ebot'
			colors = random.choice([discord.Color(0xa34142).value,
									discord.Color(0x4b4bce).value])
			d = f"The command `{ctx.command.qualified_name.split(' ')[-1]}` has reported a fatal error, " \
				f"causing it to unexpectedly quit.\n" \
				"if you would like more info or help, click [me](https://invite.gg/ebot)" \
				" or the title to join my" \
				f" support server, open a ticket with `y!bug` and tell us the error.\n\n**Your case ID is `{case_id}`." \
				" You will need this if you request support.**"
			e = discord.Embed(title="oops!", description=d, color=colors, url=url,
							timestamp=datetime.datetime.utcnow())
			e.add_field(name="Error (nerd stuff):", value=f"Error type: `{type(error)}`\n```py\n{error}\n```", inline=False)
			e.set_author(name=ctx.author.name, url=url, icon_url=ctx.guild.icon_url)
			if ctx.command.is_on_cooldown(ctx):
				e.set_footer(icon_url='https://i.dlpng.com/static/png/422758_preview.png',
							text='Your cooldown has been reset.')
				ctx.command.reset_cooldown(ctx)

			try:
				await ctx.send(embed=e)
			except (discord.Forbidden, discord.NotFound):
				pass

			raise error

	@commands.Cog.listener()
	async def on_guild_join(self,server):
		tos = f"Hello {server.owner.mention}! I have successfully joined your guild **{server.name}**! Thank you (or whoever) for adding me! However, before you continue, by having the bot actively in your server, " \
			f"you agree to the following tos, listed at [soon]. have a great time, and dont forget to check out `y!help`," \
			f" its full of useful commands for you to enjoy!*"
		try:
			await server.owner.send(tos)
		except discord.Forbidden:
			for x in server.text_channels:
				try:
					await x.send(tos)
					break
				except:
					pass
		jembed=discord.Embed(title="I joined {}!".format(server), description="Now in {} servers!".format(len(self.bot.guilds)), color=randint(0,0xffffff))
		jembed.add_field(name="Members", value=server.member_count)
		jembed.add_field(name="owner",value=server.owner)
		jembed.add_field(name="region", value=server.region)
		jembed.set_footer(text=server.id)
		jembed.set_thumbnail(url="{}".format(server.icon_url))
		d = discord.utils.get(self.bot.guilds, id=486910899756728320)
		c = discord.utils.get(d.text_channels, name="servers")
		await c.send(embed=jembed)
		await self.bot.change_presence(activity=discord.Game(name=f"{len(self.bot.guilds)} servers!"), status=None)

	@commands.Cog.listener()
	async def on_guild_remove(self, server):
		jembed=discord.Embed(title="I left {}!".format(server), description="Now in {} servers.".format(len(self.bot.guilds)),color=randint(0, 0xffffff))
		jembed.add_field(name="Members", value=server.member_count)
		jembed.add_field(name="owner",value=server.owner)
		jembed.add_field(name="region", value=server.region)
		jembed.set_footer(text=server.id)
		jembed.set_thumbnail(url="{}".format(server.icon_url))
		d = discord.utils.get(self.bot.guilds, id=486910899756728320)
		c = discord.utils.get(d.text_channels, name="servers")
		await c.send(embed=jembed)
		await self.bot.change_presence(activity=discord.Game(name=f"{len(self.bot.guilds)} servers!"), status=None)

	@staticmethod
	def message(*, event: str, location: discord.TextChannel=None, victim: discord.User=None, mod: discord.User=None, reason:str=None, message_before: discord.Message, message_after:discord.Message=None, other=""):
		a = message_after
		b = message_before
		e = discord.Embed(title=event,
						  description=f"**author:** {b.author} ({b.author.mention})\n" \
							  f"**location:** {location.mention}",
						  color=discord.Color.orange(),
						  timestamp=b.created_at)
		e.set_author(icon_url=message_before.author.avatar_url_as(format='png'), name=b.author, url=message_after.jump_url if a is not None else discord.Embed.Empty)
		e.add_field(name="Before:", value=message_before.content if len(message_before.content) <= 256 else message_before.content[:253]+'...', inline=False)
		if message_after is not None:
			e.add_field(name="After:", value=message_after.content if len(message_after.content) <= 256 else message_after.content[:253]+'...', inline=False)
		return e

	@commands.Cog.listener()
	async def on_message_edit(self, bmessage, amessage):
		if amessage.author.bot or amessage.content == bmessage.content:
			return  # dont log bots, or it was just an embed.
		if not amessage.guild.me.guild_permissions.manage_webhooks:
			return
		a = amessage
		for c in a.guild.text_channels:
			if 'y-el' in str(c.topic) or c.name == 'y-el':
				x = self.message(event="Message Edit", location=amessage.channel, message_before=bmessage, message_after=amessage)
				if len(await c.webhooks()) > 0:
					async with aiohttp.ClientSession() as session:
						web = await c.webhooks()
						webhook = Webhook.from_url(web[0].url, adapter=AsyncWebhookAdapter(session))
						await webhook.send(embed=x, username=f"{amessage.guild.me.display_name} Message Logging",
										   avatar_url=self.bot.user.avatar_url_as(format='png'))
				else:
					wh = await c.create_webhook(name=f'{self.bot.user.display_name} Message Logging', reason='Message logger couldn\'t find '
																											 'a webhook to send logs to, so it has automatically been created for you.')
					async with aiohttp.ClientSession() as session:
						webhook = Webhook.from_url(wh.url, adapter=AsyncWebhookAdapter(session))
						await webhook.send(embed=x, username=f"{a.guild.me.display_name} Message Logging",
										   avatar_url=self.bot.user.avatar_url_as(format='png'))
				return await session.close()

	@commands.Cog.listener()
	async def on_message_delete(self, message):
		if message.author.bot:
			return  # dont log bots.
		amessage = message
		if not amessage.guild.me.guild_permissions.manage_webhooks:
			return
		a = message
		for c in a.guild.text_channels:
			if 'y-el' in str(c.topic) or c.name == 'y-el':
				x = self.message(event="Message Deleted!", location=message.channel, message_before=message)
				files = []
				if len(message.attachments)>0:
					files = []
					for file in message.attachments:
						files.append(discord.File('./data/saved_images', filename=file.filename))
					x.set_author(name=f"{len(files)} recovered files ^")
				if len(await c.webhooks()) > 0:
					async with aiohttp.ClientSession() as session:
						web = await c.webhooks()
						webhook = Webhook.from_url(web[0].url, adapter=AsyncWebhookAdapter(session))
						await webhook.send(embed=x, username=f"{message.guild.me.display_name} Message Logging",
										   avatar_url=self.bot.user.avatar_url_as(format='png'))
				else:
					wh = await c.create_webhook(files=files,name=f'{self.bot.user.display_name} Message Logging', reason='Message logger couldn\'t find '
																														 'a webhook to send logs to, so it has automatically been created for you.')
					async with aiohttp.ClientSession() as session:
						webhook = Webhook.from_url(wh.url, adapter=AsyncWebhookAdapter(session))
						await webhook.send(files=files, embed=x, username=f"{message.guild.me.display_name} Message Logging",
										   avatar_url=self.bot.user.avatar_url_as(format='png'))
				if len(files) != 0:
					for file in files:
						os.remove(file.fp.name)
				return await session.close()

	@commands.Cog.listener()
	async def on_member_remove(self, member):
		if member.guild.me.guild_permissions.view_audit_log:
			if not member.guild.me.guild_permissions.manage_webhooks:
				return
			message = member
			for c in member.guild.text_channels:
				if 'y-el' in str(c.topic) or c.name == 'y-el':
					e = discord.Embed(title="Member left!", description=f"now {len(member.guild.members)} members.", color=discord.Color.red())
					e.set_thumbnail(url=str(member.avatar_url).replace('.webp', '.png'))
					e.set_author(name=member.name, icon_url=member.avatar_url)
					e.add_field(name="User Roles:", value=', '.join([role.name for role in member.roles]), inline=False)
					x = e
					if len(await c.webhooks()) > 0:
						async with aiohttp.ClientSession() as session:
							web = await c.webhooks()
							webhook = Webhook.from_url(web[0].url, adapter=AsyncWebhookAdapter(session))
							await webhook.send(embed=x, username=f"{message.guild.me.display_name} Event Logging",
											   avatar_url=self.bot.user.avatar_url_as(format='png'))
					else:
						wh = await c.create_webhook(name=f'{self.bot.user.display_name} Event Logging', reason='Event logger couldn\'t find '
																											   'a webhook to send logs to, so it has automatically been created for you.')
						async with aiohttp.ClientSession() as session:
							webhook = Webhook.from_url(wh.url, adapter=AsyncWebhookAdapter(session))
							await webhook.send(embed=x, username=f"{message.guild.me.display_name} Event Logging",
											   avatar_url=self.bot.user.avatar_url_as(format='png'))
					return await session.close()

	@commands.Cog.listener()
	async def on_member_join(self, member):
		if member.guild.me.guild_permissions.view_audit_log:
			if not member.guild.me.guild_permissions.manage_webhooks:
				return
			message = member
			for c in member.guild.text_channels:
				if 'y-el' in str(c.topic) or c.name == 'y-el':
					e = discord.Embed(title="Member Joined!", description=f"now {len(member.guild.members)} members.", color=discord.Color.green())
					e.set_thumbnail(url=str(member.avatar_url).replace('.webp', '.png'))
					e.set_author(name=member.name, icon_url=member.avatar_url)
					x = e
					if len(await c.webhooks()) > 0:
						async with aiohttp.ClientSession() as session:
							web = await c.webhooks()
							webhook = Webhook.from_url(web[0].url, adapter=AsyncWebhookAdapter(session))
							await webhook.send(embed=x, username=f"{message.guild.me.display_name} Event Logging",
											   avatar_url=self.bot.user.avatar_url_as(format='png'))
					else:
						wh = await c.create_webhook(name=f'{self.bot.user.display_name} Event Logging', reason='Event logger couldn\'t find '
																											   'a webhook to send logs to, so it has automatically been created for you.')
						async with aiohttp.ClientSession() as session:
							webhook = Webhook.from_url(wh.url, adapter=AsyncWebhookAdapter(session))
							await webhook.send(embed=x, username=f"{message.guild.me.display_name} Event Logging",
											   avatar_url=self.bot.user.avatar_url_as(format='png'))
					return await session.close()

	@commands.Cog.listener()
	async def on_member_ban(self, guild, member):
		if guild.me.guild_permissions.view_audit_log:
			if not guild.me.guild_permissions.manage_webhooks or not guild.me.guild_permissions.ban_members:
				return
			message = member
			for c in guild.text_channels:
				if 'y-el' in str(c.topic) or c.name == 'y-el':
					e = discord.Embed(title="Member Banned!", description=f"now {len(await guild.bans())} bans.", color=discord.Color.red())
					e.set_thumbnail(url=str(member.avatar_url).replace('.webp', '.png'))
					e.set_author(name=member.name, icon_url=member.avatar_url)
					log = await guild.audit_logs(action=discord.AuditLogAction.ban, limit=1).flatten()
					log = log[0]
					e.add_field(name="details:", value=f"banned at: {log.created_at.strftime(self.dtf)}\nReason: {log.reason}\n**mod**: {log.user.mention} ({log.user})")
					x = e
					if isinstance(member, discord.Member):
						e.add_field(name="User Roles:", value=', '.join([role.name for role in member.roles]), inline=False)
					if len(await c.webhooks()) > 0:
						async with aiohttp.ClientSession() as session:
							web = await c.webhooks()
							webhook = Webhook.from_url(web[0].url, adapter=AsyncWebhookAdapter(session))
							await webhook.send(embed=x, username=f"{guild.me.display_name} Event Logging",
											   avatar_url=self.bot.user.avatar_url_as(format='png'))
					else:
						wh = await c.create_webhook(name=f'{self.bot.user.display_name} Event Logging', reason='Event logger couldn\'t find '
																											   'a webhook to send logs to, so it has automatically been created for you.')
						async with aiohttp.ClientSession() as session:
							webhook = Webhook.from_url(wh.url, adapter=AsyncWebhookAdapter(session))
							await webhook.send(embed=x, username=f"{guild.me.display_name} Event Logging",
											   avatar_url=self.bot.user.avatar_url_as(format='png'))
					return await session.close()

	@commands.Cog.listener()
	async def on_member_unban(self, guild, user):
		if guild.me.guild_permissions.view_audit_log:
			if not guild.me.guild_permissions.manage_webhooks or not guild.me.guild_permissions.ban_members:
				return
			member = user
			for c in guild.text_channels:
				if 'y-el' in str(c.topic) or c.name == 'y-el':
					e = discord.Embed(title="Member Unanned!", description=f"now {len(await guild.bans())} bans.", color=discord.Color.green())
					e.set_thumbnail(url=str(member.avatar_url).replace('.webp', '.png'))
					e.set_author(name=member.name, icon_url=member.avatar_url)
					log = await guild.audit_logs(action=discord.AuditLogAction.unban, limit=1).flatten()
					log = log[0]
					e.add_field(name="details:", value=f"Unbanned at: {log.created_at.strftime(self.dtf)}\nReason: {log.reason}\n**mod**: {log.user.mention} ({log.user})")
					x = e
					if len(await c.webhooks()) > 0:
						async with aiohttp.ClientSession() as session:
							web = await c.webhooks()
							webhook = Webhook.from_url(web[0].url, adapter=AsyncWebhookAdapter(session))
							await webhook.send(embed=x, username=f"{guild.me.display_name} Event Logging",
											   avatar_url=self.bot.user.avatar_url_as(format='png'))
					else:
						wh = await c.create_webhook(name=f'{guild.me.display_name} Event Logging', reason='Event logger couldn\'t find '
																										  'a webhook to send logs to, so it has automatically been created for you.')
						async with aiohttp.ClientSession() as session:
							webhook = Webhook.from_url(wh.url, adapter=AsyncWebhookAdapter(session))
							await webhook.send(embed=x, username=f"{guild.me.display_name} Event Logging",
											   avatar_url=self.bot.user.avatar_url_as(format='png'))
					return await session.close()

	@commands.Cog.listener()
	async def on_guild_role_create(self, role):
		print(2)
		if role.guild.me.guild_permissions.manage_roles:
			if not role.guild.me.guild_permissions.manage_webhooks:
				return
			await asyncio.sleep(10)
			try:
				role = role.guild.get_role(role.id)
			except discord.NotFound:
				return
			message = role
			for c in role.guild.text_channels:
				if 'y-el' in str(c.topic) or c.name == 'y-el':
					e = discord.Embed(title="Role Created!", description=f"now {len(role.guild.roles)} roles.", color=discord.Color.green())
					e.add_field(name="info:", value=f"**Name:** {role.name}\nID: {role.id}\nMentionable: {role.mentionable}\nHoisted: {role.hoist}\nCreated at: {role.created_at.strftime(self.dtf)}\n**Members:** {len(role.members)}")
					x = e
					if len(await c.webhooks()) > 0:
						async with aiohttp.ClientSession() as session:
							web = await c.webhooks()
							webhook = Webhook.from_url(web[0].url, adapter=AsyncWebhookAdapter(session))
							await webhook.send(embed=x, username=f"{message.guild.me.display_name} Event Logging",
											   avatar_url=self.bot.user.avatar_url_as(format='png'))
					else:
						wh = await c.create_webhook(name=f'{self.bot.user.display_name} Event Logging', reason='Event logger couldn\'t find '
																											   'a webhook to send logs to, so it has automatically been created for you.')
						async with aiohttp.ClientSession() as session:
							webhook = Webhook.from_url(wh.url, adapter=AsyncWebhookAdapter(session))
							await webhook.send(embed=x, username=f"{message.guild.me.display_name} Event Logging",
											   avatar_url=self.bot.user.avatar_url_as(format='png'))
					return await session.close()

	@commands.Cog.listener()
	async def on_guild_role_delete(self, role):
		print(3)
		if role.guild.me.guild_permissions.manage_roles:
			if not role.guild.me.guild_permissions.manage_webhooks:
				return
			message = role
			for c in role.guild.text_channels:
				if 'y-el' in str(c.topic) or c.name == 'y-el':
					e = discord.Embed(title="Role Deleted!", description=f"now {len(role.guild.roles)} roles.", color=discord.Color.red())
					e.add_field(name="info:", value=f"**Name:** {role.name}\nID: {role.id}\nMentionable: {role.mentionable}\nHoisted: {role.hoist}\nCreated at: {role.created_at.strftime(self.dtf)}\n**Members:** {len(role.members)}")
					x = e
					if len(await c.webhooks()) > 0:
						async with aiohttp.ClientSession() as session:
							web = await c.webhooks()
							webhook = Webhook.from_url(web[0].url, adapter=AsyncWebhookAdapter(session))
							await webhook.send(embed=x, username=f"{message.guild.me.display_name} Event Logging",
											   avatar_url=self.bot.user.avatar_url_as(format='png'))
					else:
						wh = await c.create_webhook(name=f'{self.bot.user.display_name} Event Logging', reason='Event logger couldn\'t find '
																											   'a webhook to send logs to, so it has automatically been created for you.')
						async with aiohttp.ClientSession() as session:
							webhook = Webhook.from_url(wh.url, adapter=AsyncWebhookAdapter(session))
							await webhook.send(embed=x, username=f"{message.guild.me.display_name} Event Logging",
											   avatar_url=self.bot.user.avatar_url_as(format='png'))
					return await session.close()

	@commands.Cog.listener()
	async def on_guild_role_update(self, role, arole):
		if role == role.guild.default_role:
			return
		if role.guild.me.guild_permissions.manage_roles:
			if not role.guild.me.guild_permissions.manage_webhooks:
				return
			if role.position != arole.position:  # probably position change
				return
			message = role
			for c in role.guild.text_channels:
				if 'y-el' in str(c.topic) or c.name == 'y-el':
					e = discord.Embed(title="Role Updated!", description=f"now {len(role.guild.roles)} roles.", color=discord.Color.gold())
					e.add_field(name="Before info:", value=f"**Name:** {role.name}\nID: {role.id}\nMentionable: {role.mentionable}\nHoisted: {role.hoist}\nCreated at: {role.created_at.strftime(self.dtf)}\n**Members:** {len(role.members)}")
					e.add_field(name='\u200B', value='\u200b', inline=False)
					e.add_field(name="After info:", value=f"**Name:** {arole.name}\nID: {arole.id}\nMentionable: {arole.mentionable}\nHoisted: {arole.hoist}\nCreated at: {arole.created_at.strftime(self.dtf)}\n**Members:** {len(arole.members)}")
					a=dict(arole.permissions)
					r=dict(role.permissions)
					if a != r:
						changed = []
						for name, value in dict(arole.permissions):
							if r[name] != a[name]:
								changed.append(f"{a[name]}: {a[value]}")
						e.add_field(name="permissions Changes:", value=str(' / '.join(changed))[:1024], inline=False)
					x = e
					if len(await c.webhooks()) > 0:
						async with aiohttp.ClientSession() as session:
							web = await c.webhooks()
							webhook = Webhook.from_url(web[0].url, adapter=AsyncWebhookAdapter(session))
							await webhook.send(embed=x, username=f"{message.guild.me.display_name} Event Logging",
											   avatar_url=self.bot.user.avatar_url_as(format='png'))
					else:
						wh = await c.create_webhook(name=f'{self.bot.user.display_name} Event Logging', reason='Event logger couldn\'t find '
																											   'a webhook to send logs to, so it has automatically been created for you.')
						async with aiohttp.ClientSession() as session:
							webhook = Webhook.from_url(wh.url, adapter=AsyncWebhookAdapter(session))
							await webhook.send(embed=x, username=f"{message.guild.me.display_name} Event Logging",
											   avatar_url=self.bot.user.avatar_url_as(format='png'))
					return await session.close()

	@commands.Cog.listener()
	async def on_raw_message_delete(self, msg):
		if msg.cached_message:
			return  # probably already logged

		else:
			channel = self.bot.get_channel(msg.channel_id)
			e = discord.Embed(
				title="Uncached message deleted!",
				description=f"An uncached message was deleted in {channel.mention}. That's all i know.",
				color=0x8B4513
			)
			e.add_field(name="what is caching?", value=f"*caching* is the act of storing data for a short period of "
			f"time, often removed and replaced on a refresh/reboot. to keep our filesize low, we lower our max_messages "
			f"cache. if this is bothering you, ask my dev to increase the 'max_messages' paramater on me! im currently "
			f"set to cache {self.bot.max_messages} messages, and have cached {len(self.bot.cached_messages)}/"
			f"{self.bot.max_messages} messages.")
			for c in channel.guild.text_channels:
				if 'y-el' in str(c.topic) or c.name == 'y-el':
					x = e
					if len(await c.webhooks()) > 0:
						async with aiohttp.ClientSession() as session:
							web = await c.webhooks()
							webhook = Webhook.from_url(web[0].url, adapter=AsyncWebhookAdapter(session))
							await webhook.send(embed=x, username=f"{channel.guild.me.display_name} Event Logging",
											   avatar_url=self.bot.user.avatar_url_as(format='png'))
					else:
						wh = await c.create_webhook(name=f'{self.bot.user.display_name} Event Logging', reason='Event logger couldn\'t find '
																											   'a webhook to send logs to, so it has automatically been created for you.')
						async with aiohttp.ClientSession() as session:
							webhook = Webhook.from_url(wh.url, adapter=AsyncWebhookAdapter(session))
							await webhook.send(embed=x, username=f"{channel.guild.me.display_name} Event Logging",
											   avatar_url=self.bot.user.avatar_url_as(format='png'))
					return await session.close()

	@commands.Cog.listener()
	async def on_bulk_message_delete(self, messages):
		async with aiohttp.ClientSession() as session:
			e = discord.Embed(title="Bulk delete", description=f"{len(messages)} messages deleted in "
															f"{messages[0].channel.mention}. click my url for contents.")
			fmt = []
			session = session
			for message in messages:
				if len(fmt) == 0:
					fmt.append(f"\n{message.author} {message.created_at.strftime(self.dtf)}:\n{message.content}")
				elif fmt[-1].startswith(str(message.author)):
					fmt.append(f"{message.content}")
				else:
					fmt.append(f"\n{message.author} {message.created_at.strftime(self.dtf)}:\n{message.content}")
			d = await session.post('https://mystb.in/documents', data=bytes(''.join(fmt).encode('utf-8')))
			z = await d.json()
			e.url = f'https://mystb.in/{z["key"]}.md'

			for c in messages[0].guild.text_channels:
				if 'y-el' in str(c.topic) or c.name == 'y-el':
					x = e
					if len(await c.webhooks()) > 0:
						web = await c.webhooks()
						webhook = Webhook.from_url(web[0].url, adapter=AsyncWebhookAdapter(session))
						await webhook.send(embed=x, username=f"{messages[0].guild.me.display_name} Event Logging",
										   avatar_url=self.bot.user.avatar_url_as(format='png'))
					else:
						wh = await c.create_webhook(name=f'{self.bot.user.display_name} Event Logging',
														reason='Event logger couldn\'t find '
															'a webhook to send logs to, so it has automatically been created for you.')
						webhook = Webhook.from_url(wh.url, adapter=AsyncWebhookAdapter(session))
						await webhook.send(embed=x, username=f"{messages[0].guild.me.display_name} Event Logging",
										   avatar_url=self.bot.user.avatar_url_as(format='png'))
		return await session.close()


def setup(bot):
	bot.add_cog(ErrorHandler(bot))
