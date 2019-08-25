import discord, typing, asyncio, aiohttp, os

from cogs.config import json_mngr
from utils.errors import GetError
from utils.page import pagify
from discord.ext import commands


class ServerManagement(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	async def addemoji_method(self, ctx, *, data: dict, emoji: discord.Emoji):
		"""
		add an emoji
		:param ctx: commands.Context
		:param data: dict
		:param emoji: discord.Emoji
		:returns: discord.Message
		"""
		te = discord.utils.get(self.bot.emojis, id=data[str(emoji.id)]['id'])
		if te is None:
			raise GetError(code=1, reason="This emoji is no longer available (not found)")

		if '.gif' in str(te.url):
			ending = '.gif'
		else:
			ending = '.png'

		try:
			await ctx.guild.create_custom_emoji(name=te.name, image=await te.url.read(), reason=
			f"Added by {ctx.author} from {te.guild.name}")
			return await ctx.send("success!")
		except:
			with open(f'./data/emojis/{te.id}{ending}', 'w+') as nemoji:
				await te.url.save(nemoji)
				await asyncio.sleep(2)
				saved = await ctx.guild.create_custom_emoji(name=te.name, image=nemoji.read(), reason=
				f"Added by {ctx.author} from {te.guild.name}")
			if saved > 256000:  # remove it if its greater then 256kb large.
				os.remove(f'./data/emojis/{te.id}{ending}')
			return await ctx.send("Added emoji!")

	@commands.group(case_insensitive=True, invoke_without_command=True)
	async def addemoji(self,ctx, emoji: typing.Union[int, str]=None):
		"""Add an emoji from our list!"""
		data = json_mngr().read('./data/emojis.json')
		if emoji:
			for name in data.keys():
				if isinstance(emoji, int) and emoji == data[name]['id']:
					te = discord.utils.get(self.bot.emojis, id=emoji)
					if te is None:
						raise GetError(code=1, reason='This emoji is unavailable (NotFound)')
					await self.addemoji_method(ctx, emoji=te, data=data)
				else:
					tea = discord.utils.get(self.bot.emojis, name=emoji)
					for te in tea:
						if isinstance(te, discord.Emoji):
							steven = await ctx.send(f"Is this the correct emoji? [y/n]\nPreview: {te}")
							try:
								def check(m):
									return (m.author, m.channel) == (ctx.author, ctx.channel) and (
											'y' in m.content.lower() or 'y' in m.content.lower())
								bob = await self.bot.wait_for('message', check=check, timeout=120)
							except asyncio.TimeoutError:
								return await steven.edit(content="Timed out.")
							if bob.content.lower().startswith('n'):
								await bob.edit(content="Finding another one.")
								continue
							elif bob.content.lower().startswith('y'):
								return await self.addemoji_method(ctx, data=data, emoji=te)
						else:
							return await ctx.send("An unknown error caused this emoji to go unavailable\n"
													"Error code #0002")
					else:
						raise GetError(code=3, reason="Emoji not found")
		else:
			topag = ""
			for emoji in data.keys():
				topag += f"Emoji name: {emoji}\nSource guild: {emoji['guild']}\nPreview: <{emoji['url']}>\n\n"
			if len(topag) > 1900:
				for page in pagify(topag, escape_stuff=True, page_length=1900):
					await ctx.send(page, delete_after=30)
			else:
				return await ctx.send(discord.utils.escape_markdown(discord.utils.escape_mentions(topag)))

	@addemoji.command(name="add", aliases=['create', 'submit'])
	async def addemoji_add(self, ctx, emoji: discord.Emoji):
		"""Add an emoji to the emojis to be able to use that emoji

		idfk it adds the emoji for the base command"""
		data = json_mngr().read('./data/emojis.json')
		if str(emoji.id) in data.keys():
			return await ctx.send("We already have that emoji!")
		data[str(emoji.id)] = {
			"id": emoji.id,
			"url": str(emoji.url),
			"name": emoji.name,
			"guild": ctx.guild.name,
			'submitter': str(ctx.author)
		}
		json_mngr.handle_modify('./data/emojis.json', newdata=data, backup=True)
		await ctx.send("Added to the list.")

def setup(bot):
	bot.add_cog(ServerManagement(bot))


