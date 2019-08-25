import discord
import asyncio

from random import choice, randint
from datetime import datetime
from discord.ext import commands, tasks


class FightMeta:
	pass


def _e(n: str):
	return n.replace('@', '@\u200B')


class Fun(commands.Cog):

	def __init__(self, bot):
		self.bot = bot
		bot.remove_command('ball')

	async def cog_check(self, ctx):
		perms = ctx.channel.permissions_for(ctx.guild.me)
		return perms.administrator or (perms.send_messages and perms.embed_links)

	@commands.command(hidden=True)
	@commands.is_owner()
	async def emojipost(self, ctx):
		"""Fancy post the emoji lists"""
		emojis = sorted([e for e in self.bot.emojis], key=lambda e: e.name)
		paginator = commands.Paginator(suffix='', prefix='')
		channel = ctx.channel

		for emoji in emojis:
			paginator.add_line(f'{emoji} -- `{emoji}`')

		for page in paginator.pages:
			await channel.send(page)

	@commands.command(name='8ball')
	async def _ball(self, ctx, *, question: str):
		"""Ask the magical 8 ball a question to test your luck!"""
		if not question.endswith('?'):
			return await ctx.send("End your question with the correct punctuation! (you forgot the ?)")

		responses = ["yes", "no", "It is certain!", "I'd say so.", "Potentially.", "doubt it.", "ask again later.", "nah.",
					"let me think... No.", "Certainly not!"]
		resp = ''
		for i in range(len(question)):
			resp = choice(responses)
		e = discord.Embed(title=ctx.message.clean_content, description='8ball says... ' + resp, color=discord.Color.green(),
						datetime=datetime.utcnow(), url="http://dragdev.xyz/ylb")
		await ctx.send(embed=e)


def setup(bot):
	bot.add_cog(Fun(bot))
