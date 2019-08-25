import discord, random, matplotlib.pyplot as mpl
from discord.ext import tasks, commands

class CoolName(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.y = []
		self.count = 0
		self.run = 0
		self.x = []

		# msgs

		self._count = 0
		self._x = []
		self._y = []

	@commands.Cog.listener()
	async def on_command(self, ctx):
		self.count += 1

	@commands.Cog.listener()
	async def on_message(self, msg):
		self._count += 1

	@tasks.loop(seconds=5)
	async def dataupdater(self):
		self.run += 1
		self.y.append(self.count)
		self.x.append(self.run)

		self._x.append(self._count)
		self._y.append(self.run)

	@commands.command(hidden=True)
	async def stats(self, ctx):
		"""get msg stats"""
		mpl.plot(self.x, self.y)
		mpl.title("Command usage")
		mpl.xlabel("seconds since load")
		mpl.plot(self._x, self._y, color='g')
		mpl.show()


def setup(bot):
	bot.add_cog(CoolName(bot))
