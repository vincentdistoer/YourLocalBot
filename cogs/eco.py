import asyncio
import json
import logging as logger
import random
import typing
from typing import Optional, Union

from cogs.config import json_mngr
import discord
from discord.ext import commands, tasks
from discord.ext.commands import BucketType, cooldown
import datetime

import utils
from utils import checks, errors, formatting, page


class PartialCtx:
	def __init__(self, author=None, channel=None, message=None, command=None):
		self._author = author
		self._channel = channel
		self._message = message
		self._command = command

	@property
	async def author(self):
		return self._author

	@property
	def channel(self):
		return self._channel

	@property
	def message(self):
		return self._message

	@property
	def command(self):
		return self._command


def has_account():
	def predicate(ctx):
		with open('./data/eco.json', 'r') as d:
			data = json.load(d)
			return str(ctx.author.id) in data.keys()
	return commands.check(predicate)


def handle_mod(*, ctx: commands.Context=None, target: Union[discord.User, discord.Member], operation, to_change: int):
	with open('./data/eco.json', 'r') as cur:
		current = json.load(cur)
		if not str(target.id) in current.keys():
			raise errors.HasNoAccount(f"User {target} does not have an account in the database.")
		with open('./data/eco.json', 'w') as new:
			if operation == '-':
				operation = current[str(target.id)] - to_change
			else:
				operation = current[str(target.id)] + to_change
			current[str(target.id)]=operation
			json.dump(current, new)
	return current[str(target.id)]

class Eco(commands.Cog):
	"""coooool"""

	def __init__(self, bot):
		self.bot = bot
		self.coin = '<:idle:551164099099230214>'
		self.success = '<:success:522078924432343040>'
		self.loading = '<a:loading20:553253741311295498>'
		self._loading = '<a:loading:551413963766890527>'
		self.error = '<:fail:522076877075251201>'
		self.betting = {}
		self.b.start()
		self.money_pool = {"amount": 0, 'users': [], 'userbets': {}}
		d = json_mngr().read('./data/event.json')
		self.event_multi = d['event_multi']
		self.redeemed = []
		self.code = d['redeem_codes']
		self.getnewcodeauto.start()

	@staticmethod
	def _check_for_account(user):
		"""check if the user has an account."""
		with open('./data/eco.json', 'r') as x:
			y = json.load(x)
			if not str(user.id) in y.keys():
				y[str(user.id)] = 0
				json.dump(y, x)
			y = json.load(x)
			return str(user.id) in y.keys()

	@commands.command(aliases=['bal'])
	@cooldown(1, 3, BucketType.user)
	@has_account()
	async def balance(self, ctx, user: typing.Union[discord.Member, discord.User]=None):
		"""
		check a balance!

		mention someone, provide their id or name#amndtag to get that user's balance.
		"""
		user = user if user else ctx.author
		with open('./data/eco.json', 'r') as data:
			ecodata = json.load(data)
			logger.info(f"{ctx.author} successfully loaded eco.json (bal)")
		if user:
			if str(user.id) not in ecodata.keys():
				e = discord.Embed(
					title="That user is not in the LocalBank:tm:!",
					color=discord.Color.purple()
				)
				e.set_footer(text=f"Maybe tell them to run '{ctx.prefix}register'?")
				return await ctx.send(embed=e)
			else:
				e = discord.Embed(
					title=f"{user.name}'s balance:",
					description=f"{self.coin} {ecodata[str(user.id)]}",
					color=discord.Color.orange()
				)
				return await ctx.send(embed=e)
		else:
			if str(ctx.author.id) not in ecodata.keys():
				e = discord.Embed(
					title="You dont have an account with the LocalBank:tm:!",
					color=discord.Color.purple()
				)
				e.set_footer(text=f"Maybe run '{ctx.prefix}register'?")
				return await ctx.send(embed=e)
			else:
				user = ctx.author
				e = discord.Embed(
					title=f"{user.name}'s balance:",
					description=f"{self.coin} {ecodata[str(user.id)]}",
					color=discord.Color.orange()
				)
				return await ctx.send(embed=e)

	@commands.command()
	async def lb(self, ctx):
		"""get the global leaderboard"""
		my_dict = json_mngr().read('./data/eco.json')
		d = ""
		sort = list(reversed(sorted(my_dict.keys(), key=lambda x: my_dict[x])))
		for num, user in enumerate(sort[:10], start=1):
			try:
				us = self.bot.get_user(int(user))
				u = discord.utils.escape_mentions(discord.utils.escape_markdown(us.display_name))
			except discord.NotFound:
				u = '*unknown user'
				us = await self.bot.fetch_user(int(user))
			d += f'**{num}**. {u}: {self.coin}{my_dict[str(us.id)]}\n'
		e = discord.Embed(
			title="YourLocalEco! leaderboard:",
			description=d,
			color=discord.Color.blue()
		)
		await ctx.send(embed=e)

	@commands.command()
	@cooldown(1, 3, BucketType.user)
	async def register(self, ctx):
		"""
		Create an account in the LocalBank:tm:!
		"""
		msg = await ctx.send(f'{self._loading} opening database')
		await asyncio.sleep(.25)
		with open('./data/eco.json', 'r+') as data:
			await msg.edit(content=f"{self._loading} loading data")
			new_data = json.load(data)
			if str(ctx.author.id) in new_data.keys():
				await msg.edit(content=f'<a:typing:599183913889431603> Are you sure you would like to reset your balance of {self.coin}{new_data[str(ctx.author.id)]}? [y/n]')
				x = await self.bot.wait_for('message', check=lambda m: m.channel == ctx.channel and m.author == ctx.author)
				if x.content.lower().startswith('y'):
					pass
				else:
					return await msg.edit(content=f"{self.success} cancelled reset.")
			new_data[str(ctx.author.id)] = 0
			await asyncio.sleep(.4)
			await msg.edit(content=f"{self._loading} saving data")
			with open('./data/eco.json', 'w+') as data:
				json.dump(new_data, data)
		await msg.edit(content=f"{self.success} Successfully opened a new bank account!")
		logger.info(f"{ctx.author} successfully made an account")

	@commands.command()
	@cooldown(1, 60, BucketType.user)
	@has_account()
	async def work(self, ctx):
		"""earn some money!

		Yields: 20-200 coins
		"""
		with open('./data/eco.json', 'r+') as data:
			earned = random.randint(20, 200)
			new_data = json.load(data)
			if str(ctx.author.id) not in new_data.keys():
				return await ctx.send(f"{self.error} You aren't registered! do {ctx.prefix}register")
			new_file = open('./data/eco.json', 'w+')
			new_data[str(ctx.author.id)] += earned
			json.dump(new_data, new_file)
			new_file.close()
		await ctx.send(embed=discord.Embed(
			description=f"You worked and earned {self.coin}{earned}.",
			color=discord.Color.orange()
		))

	async def cog_command_error(self, ctx, error):
		error = getattr(error, 'original', error)
		if isinstance(error, json.decoder.JSONDecodeError) and 'Extra data'.lower() in str(error).lower() or "Expecting value" in str(error):
			return await ctx.send(f"***ERROR: THE DATABASE IS CORRUPTED; PLEASE ALERT MY DEVELOPER __IMMEDIATELY!!!__***")

	@commands.group(invoke_without_command=True)
	async def shop(self, ctx):
		"""
		list shop items!

		do not supply an argument. use `shop buy` subcommand to buy something
		"""
		with open('./data/shop.json', 'r') as data:
			disp = json.load(data)
		with open('./data/eco.json', 'r') as data:
			data = json.load(data)
		if str(ctx.author.id) not in data.keys():
			bal = 0
		else:
			bal = data[str(ctx.author.id)]
		n = await ctx.send(f'{self._loading} constructing...')
		e = discord.Embed(title=f"{ctx.guild}s shop:", description=f"You have: {self.coin}{bal}", color=discord.Color.orange())
		try:
			for field in disp[str(ctx.guild.id)]:
				e.add_field(name=f"{field['name']} - {self.coin}{field['price']}", value=field['description'], inline=False)
		except KeyError as ee:
			e.add_field(name="This guild has no items!", value=f"try doing `shop create`.\n{ee}")
		e.set_footer(text="wip")
		await n.edit(content=None, embed=e)

	@shop.command(aliases=['add'])
	@checks.mod_or_permissions(manage_guild=True)
	async def create(self, ctx, cost:typing.Optional[int],*, contents:commands.clean_content):
		"""
		Make an item on theshop!
		"""
		cost = cost if cost else 1000
		with open('./data/shop.json', 'r+') as file:
			js = json.load(file)
			stuff = str(contents).split('<##>')
			if len(stuff) != 2:
				return await ctx.send("please put `<##>` in your text to split into name "
									  "and description.\nExample:\n```Name here<##>Description here```")
			field = {}
			field['name'] = stuff[0]
			field['price'] = cost
			field['description'] = stuff[1]
			e = discord.Embed(title=f"{ctx.guild}s shop:", description=f"You have: {self.coin}1234", color=discord.Color.orange())
			e.add_field(name=f"{field['name']} - {self.coin}{field['price']}", value=field['description'], inline=False)
			asdf = await ctx.send('Does this look right? [y/n]',embed=e)
			y = await self.bot.wait_for('message', check=lambda m: m.author==ctx.author and m.channel==ctx.channel)
			if y.content.lower().startswith('y'):
				if str(ctx.guild.id) not in js.keys():
					js[str(ctx.guild.id)] = []
				js[str(ctx.guild.id)].append(
					{
						"name": field['name'],
						"price": cost,
						"description": field['description']
					}
				)
				with open('./data/shop.json', 'w') as file:
					json.dump(js, file)
				try:
					await y.delete()
				except:
					pass
			await asdf.edit(content="Added {0} to the list, view it on `{1}shop`!".format(stuff[0], ctx.prefix))
	@shop.command(aliases=['remove'])
	@commands.has_permissions(manage_guild=True)
	async def rem(self, ctx, *, name: commands.clean_content):
		"""
		Remove item on theshop!
		"""
		with open('./data/shop.json', 'r+') as filee:
			js = json.load(filee)
			it = str(ctx.guild.id)
			if it in js.keys():
				if js[it] == []:
					return await ctx.send("Your shop is already empty! \U0001f578")
				else:
					for item in js[it]:
						if name in item.values():
							await ctx.send(f'Are you sure you want to delete {name}?')
							conf = await self.bot.wait_for('message', check=lambda n: n.author == ctx.author and n.channel == ctx.channel)
							if conf.content.lower().startswith('y'):
								js[it].remove(item)
								with open('./data/shop.json', 'w+') as file:
									json.dump(js, file)
								return await conf.add_reaction(self.success)
							else:
								return await conf.add_reaction('\U000023f8')
					else:
						await ctx.send(f'Itterator ran out of entries to scan through. {name} must not exist.')
			else:
				return await ctx.send('Your shop is already empty! \U0001f578')

	@shop.command(name="reset")
	@commands.has_permissions(administrator=True)
	async def _reset(self, ctx):
		"""
		reset the ENTIRE shop
		**WARNING:** __this action is **IRREVERSIBLE** and once you run this command, no recovery is possible.__
		"""
		with open('./data/shop.json', 'r+') as filee:
			js = json.load(filee)
			it = str(ctx.guild.id)
			if it in js.keys():
				if js[it] == []:
					return await ctx.send("Your shop is already empty! \U0001f578")
				else:
					js[it] = []
					with open('./data/shop.json', 'w+') as file:
						json.dump(js, file)
					await ctx.message.add_reaction(self.success
												   )
			else:
				return await ctx.send('Your shop is already empty! \U0001f578')

	@shop.command(hidden=True)
	@has_account()
	@commands.cooldown(5, 5, BucketType.user)
	async def buy(self, ctx, item_name: commands.clean_content):
		"""
		Buy something!
		***THERE IS NO INVERNTORY SYSTEM AND THIS COMMAND IS PURELY ABSTRACT. IT WILL STILL DEDUCT YOUR BALANCE.***
		"""
		with open('./data/shop.json', 'r') as a:
			x = json.load(a)
			g = str(ctx.guild.id)
			if g not in x or str(item_name).lower() not in x[g][0]['name'].lower():
				return await ctx.send("Item not found.")
			else:
				try:
					z=handle_mod(ctx=ctx, target=ctx.author, operation='-', to_change=x[g][0]['price'])
					await ctx.send(f"{self.success} bought {item_name} for {self.coin}{z}.")
				except errors.HasNoAccount:
					await ctx.send("Please register an account first.")

	@commands.command(aliases=['roullette', 'roulete', 'roullet', 'icantspellroulette','gamble'])
	@cooldown(5, 5, BucketType.user)
	@has_account()
	async def roulette(self, ctx, amount: int = 100, Space: str = 'even'):
		"""
		gamble some money for a chance to win more!

		Minimum bet: 50
		Maximum bet: 10,000
		Space: `odd`/`even`
		"""
		if str(amount).startswith('-'):
			return await ctx.send("You cant bet negatives!")
		with open('./data/eco.json', 'r') as x:
			y = json.load(x)
			if y[str(ctx.author.id)] < amount:
				return await ctx.send(f"You only have {self.coin}{y[str(ctx.author.id)]}!")
		m = await ctx.send("Spinning...\n*Speed mode!*")
		await asyncio.sleep(2.5)
		space = Space.lower()
		if space not in ['even', 'odd']:
			return await m.edit(content="You lost!\n\nNext time supply `even` or `odd` after your bet.")
		ch = random.choice(['odd', 'even'])
		if ch == space:
			with open('./data/eco.json', 'r') as filee:
				js = json.load(filee)
				js[str(ctx.author.id)] += round(amount * 2.5)
				with open('./data/eco.json', 'w+') as filee:
					json.dump(js, filee)
			await m.edit(content=f"You won! +{self.coin}{round(amount*2.5)}")
		else:
			with open('./data/eco.json', 'r') as filee:
				js = json.load(filee)
				js[str(ctx.author.id)] -= round(amount * 2.5)
				with open('./data/eco.json', 'w+') as filee:
					json.dump(js, filee)
			await m.edit(content=f"You lost. -{self.coin}{round(amount*2.5)}")

	@commands.command(hidden=True)
	@checks.co_owner()
	async def addmoney(self, ctx, user: discord.User, amount: int):
		"""Add money to an account!"""
		with open('./data/eco.json', 'r') as x:
			y = json.load(x)
			with open('./data/eco.json', 'w') as z:
				y[str(user.id)] += amount
				json.dump(y, z)
		return await ctx.message.add_reaction(self.success)

	@commands.command(hidden=True, name='rem')
	@checks.co_owner()
	async def remmoney(self, ctx, user: discord.User, amount: int):
		"""Add money to an account!"""
		with open('./data/eco.json', 'r') as x:
			y = json.load(x)
			with open('./data/eco.json', 'w') as z:
				y[str(user.id)] -= amount
				json.dump(y, z)
		return await ctx.message.add_reaction(self.success)

	@commands.group(invoke_without_command=True)
	async def pool(self, ctx, amount: int = 1000):
		"""
		put money into a pool.
		a user will be picked at random every 2 minutes and will win the entire pool back.
		"""
		x = handle_mod(ctx=ctx, target=ctx.author, operation='+', to_change=0)
		if x < amount:
			return await ctx.send(f"You don't have enough to bet that much!\nYou need {self.coin}{amount-x} more!")
		elif amount < round(self.money_pool['amount'] / 3) and amount != 0:
			return await ctx.send(f"You must bet at least a third of the current pool ({self.coin}{round(self.money_pool['amount'])})!")
		elif ctx.author in self.money_pool['users']:
			if amount == 0:
				await ctx.send("Removed your bet of {}{}".format(self.coin, self.money_pool['userbets'][ctx.author]))

			c = await ctx.send(f"set your bet to {self.coin}{amount}.")
			toadd = self.money_pool['userbets'][ctx.author]
			self.money_pool['amount'] -= toadd
			new = handle_mod(target=ctx.author, operation='+', to_change=toadd)
			if new < amount:
				return await c.edit(content="You need {}{} more to set that bet!".format(self.coin, amount-new))
			self.money_pool['amount'] += amount
			self.money_pool['userbets'][ctx.author] = amount
			handle_mod(target=ctx.author, operation='-', to_change=amount)

		else:
			handle_mod(ctx=ctx, target=ctx.author, operation = '-', to_change=amount)
			self.money_pool['amount'] += amount
			self.money_pool['userbets'][ctx.author] = amount
			self.money_pool['users'].append(ctx.author)
			return await ctx.send(f"{self.success} added {self.coin}{amount} to the pool, bringing it's "
								  f"total value up to {self.coin}{self.money_pool['amount']}!")

	@pool.command()
	async def view(self, ctx):
		"""
		view the current pool value
		"""
		e = discord.Embed(
			title=f"Betters: {len(self.money_pool['users'])}",
			description=f"Current worth: {self.money_pool['amount']}\nMoney required to enter: {int(self.money_pool['amount'] / 3)}",
			color=discord.Color.gold()
		)
		if self.event_multi > 0:
			e.set_footer(text=str(self.event_multi) + 'x multiplier!')
		await ctx.send(embed=e)

	@commands.command()
	async def give(self, ctx, to: discord.User, amount: typing.Union[int, str]):
		"""Give some of your money to someone else!"""
		if to == ctx.author:
			return await ctx.send("You cant pay yourself!")
		current = handle_mod(ctx=ctx, target=ctx.author, operation='+', to_change=0)  # returns balance
		if str(amount).lower() == 'all':
			amount = current
		if amount > current:
			return await ctx.send("You don't have enough for that!")
		added = handle_mod(ctx=ctx, target=to, operation='+', to_change=amount)
		try:
			await to.send(f"{ctx.author.mention} gave you {self.coin}{amount}! you now have {self.coin}{added}.")
		except (discord.Forbidden, discord.NotFound, discord.HTTPException):
			pass
		await ctx.send(f"{self.success} {to.display_name} has received your {self.coin}{amount}")

	@commands.command()
	async def redeem(self, ctx, *, code: str):
		"""redeem a code for today only!"""
		if len(code) != len(self.code):
			await ctx.send("invalid code.")
		elif code != self.code:
			await ctx.send("invalid code.")
		else:
			if ctx.author in self.redeemed:
				return await ctx.send("You already redeemed the code!")
			handle_mod(ctx=ctx, target=ctx.author, operation='+', to_change=5000)
			self.redeemed.append(ctx.author)
			await ctx.send("redeemed!")
	@commands.command()
	@commands.is_owner()
	async def newcode(self, ctx, regen: bool = True):
		"""generate a new code for redeem"""
		if regen:
			code = await self._rand_code(ctx)
			self.code = code
			await ctx.author.send(self.code)
		else:
			await ctx.author.send(self.code)

	@tasks.loop(hours=6)
	async def getnewcodeauto(self):
		self.code = await self._rand_code()
		self.redeemed = []

	@tasks.loop(minutes=2)
	async def b(self):
		# === 'pool' win ===

		if len(self.money_pool['users']) <= 1:
			return
		try:
			winner = random.choice(self.money_pool['users'])
		except:
			return
		if self.event_multi > 1:
			self.money_pool *= self.event_multi
		handle_mod(target=winner, operation='+', to_change=self.money_pool['amount'])
		try:
			await winner.send(f"You won {self.coin}{self.money_pool['amount']} from your pool bet!")
		except:
			pass
		self.money_pool['users'].remove(winner)
		for user in self.money_pool['users']:
			try:
				await user.send(f"You lost your pool bet! try again next time.")
			except:
				continue
		self.money_pool = {"amount": 0, 'users': [], 'userbets': {}}

	def cog_unload(self):
		self.b.stop()
		self.getnewcodeauto.stop()

	async def _rand_code(self, ctx=None):
		a = list('abcdefghijklmnopqrstuvwxyz')
		b = [1,2,3,4,5,6,7,8,9,0]
		x = []
		for i in range(25, 0):
			if True:
				pass
			x.append(c)
		if ctx:
			await ctx.send(x)
		return ''.join(x)


def setup(bot):
	bot.add_cog(Eco(bot))
