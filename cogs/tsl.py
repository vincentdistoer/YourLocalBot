import discord, asyncio, typing
import time
import json
from discord.ext import commands

class TSL(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.rank_info = {
			"leader": "This is the role for the faction leader & founder. nothing special. highest in command.",
			"co-leader": "The role for the leader's assistant(s). they play a big role in decision making.",
			"high command": "High command officers; these people oversee plans, constructions, battles and resources, and occasionally base management.",
			"captain": "Usually pilots large-grid ships, sits in the control room and gives instructions to pilots. also has full control over the ship they are in, and can overrule any decisions (within reason) from ranks below theirs.",
			"officer": "Commonly pilots ships, and is in charge of ammunition control, ship security and turret control.",
			"commander": "construction, and tells the **boarding party** [rank] what to do and extraction locations. also primary gunmen. ",
			"recruit": "Usually just joined the ranks, does all the dirty work like mining and resource delivery. also can be assistant crew of ships, or pilots of fighter-class ships.",
			"boarding party": "Tasked with boarding enemy ships, disabling key components and looting, killing any enemy ship crew they find. these people are armed with top notch gear when on a boarding quest.\n\n*this rank is brutal and tough. this rank is not earned and must be applied for.*",
			"discord staff": "have ban and kick permission along with any perms their in-game rank provides them with. these just moderate the server and enforce rules."
		}
		self.channel_requests = []

	async def cog_check(self, ctx):
		return ctx.guild.id == 600072698869317645

	@commands.command()
	async def rankinfo(self, ctx, *, rank: typing.Union[discord.Role, str] = None):
		"""Get info about said rank
		rank takes a ROLE
		"""
		ranks = ["leader", "co-leader", "high command", "captain", "officer", "commander", "recruit","Boarding party", "discord staff"]
		if isinstance(rank, str):
			roles = [role.name.title() for role in ctx.guild.roles]
			rank = discord.utils.get(roles, name=rank.lower().title())
			if rank is None:
				return await ctx.send(f"{discord.utils.escape_mentions(rank.name)} was not found in our list of ranks! Available ranks below:\n`{', '.join(ranks)}`")
		if rank.name.lower() not in ranks:
			return await ctx.send(f"{discord.utils.escape_mentions(rank.name)} was not found in our list of ranks! Available ranks below:\n`{', '.join(ranks)}`")
		e = discord.Embed(
			title=rank.name,
			description=self.rank_info[rank.name.lower()],
			color=discord.Color.blue(),
			timestamp = rank.created_at
		)
		return await ctx.send(embed=e)

	@commands.group(invoke_without_command=True, case_insensitive=True, aliases=['rq', 'getchannel', 'tempchan'])
	@commands.guild_only()
	async def requestchannel(self, ctx, invited_users: commands.Greedy[discord.Member], *, reason: str):
		"""request a private channel for you and [invited_users]."""
		if len(invited_users) == 0:
			return await ctx.send("0 invited users found. please try again.")
		_id = ctx.message.id
		__id = f"{ctx.channel.id}-{ctx.message.id}"
		with open('./data/tsl.json', 'r') as asdf:
			data = json.load(asdf)
			new = {
				"id": _id,
				"get_id": __id,
				"invited_users": [_.id for _ in invited_users],  # make it json compatible
				"author": ctx.author.id,
				"reason": reason
			}
			data['channel_requests'].append(new)
			with open('./data/tsl.json', 'w') as fdsa:
				json.dump(data, fdsa)

		chan = ctx.guild.get_channel(609869595477540876)
		if chan is None:
			return await ctx.send("Unhandled type recieved, forcing command to quit\nyour submission has still been"
								" saved.")
		fmt = ""
		fmt += f"id: {_id}\nInvited Users: {', '.join(invited_users)}"
		e = discord.Embed(
			title="channel request",
			description=fmt,
			color=ctx.author.color
		)
		await chan.send(embed=e)
		await ctx.send("Submitted.")

def check_files():
	try:
		x = open('./data/tsl.json', 'r')
		x.close()
	except FileNotFoundError:
		x = open('./data/tsl.json', 'w+')
		x.write('{}')
		x.close()


def setup(bot):
	check_files()
	bot.add_cog(TSL(bot))