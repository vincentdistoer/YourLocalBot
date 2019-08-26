import discord
from discord.ext import commands
# im here for the def()s
# lif of items here:
# check_permission(perms)
# has_permissions(perms)
# check_guild_permissions(


def check_permissions(ctx, perms, *, check=all):
	resolved = ctx.channel.permissions_for(ctx.author)
	return check(getattr(resolved, name, None) == value for name, value in perms.items())


def has_permissions(*, check=all, **perms):
	async def pred(ctx):
		return check_permissions(ctx, perms, check=check)
	return commands.check(pred)


async def check_guild_permissions(ctx, perms, *, check=all):
	if ctx.guild is None:
		return False

	resolved = ctx.author.guild_permissions
	return check(getattr(resolved, name, None) == value for name, value in perms.items())


def has_guild_permissions(*, check=all, **perms):
	async def pred(ctx):
		return await check_guild_permissions(ctx, perms, check=check)
	return commands.check(pred)

# These do not take channel overrides into account


def is_mod():
	async def pred(ctx):
		return await check_guild_permissions(ctx, {'kick_members=True': True})
	return commands.check(pred)


def is_admin():
	async def pred(ctx):
		return await check_guild_permissions(ctx, {'administrator': True})
	return commands.check(pred)


def mod_or_permissions(**perms):
	perms['kick_members'] = True
	async def predicate(ctx):
		return await check_guild_permissions(ctx, perms, check=any)
	return commands.check(predicate)


def admin_or_permissions(**perms):
	perms['administrator'] = True
	async def predicate(ctx):
		return await check_guild_permissions(ctx, perms, check=any)
	return commands.check(predicate)

def gowner():
	def p(ctx):
		return ctx.author == ctx.guild.owner
	return commands.check(p)

def co_owner():
	def predicate(ctx):
		c = {
			179049652606337024: "BxPanxi",
			421698654189912064: "EEk",
			291933031919255552: "Penguin113",
			493790026115579905: "Elemental",
			344878404991975427: "chromebook777",
			414746664507801610: "Scientific Age",
			293066151695482882: "inside dev",
			269340844438454272: "shiatryx or whatever hes called now"
		}
		ctx.bot.all_owners = c
		return ctx.author.id in list(c.keys()) or ctx.author.id == ctx.bot.owner_id
	return commands.check(predicate)


def owner():
	def p(ctx):
		return ctx.author.id == ctx.bot.owner_id
	return commands.check(p)


def support_guild():
	def p(ctx):
		return ctx.guild.id == 486910899756728320
	return commands.check(p)


def modplus():
	async def pred(ctx):
		return is_mod() or is_admin()
	return commands.check(pred)


def gcmod():
	def predicate(ctx):
		g = ctx.bot.get_guild(486910899756728320)
		roles = [566471635591233538, 566471677941121025, 566471697679777802, 566471697679777802, 566471715513958400]
		for role in roles:
			ctx.author = g.get_member(ctx.author.id)
			if role in [x.id for x in ctx.author.roles]:
				return True
		else:
			return False
	return commands.check(predicate)


def gcadmin():
	def predicate(ctx):
		g = ctx.bot.get_guild(486910899756728320)
		roles = [566471677941121025, 566471697679777802, 566471697679777802, 566471715513958400]
		for role in roles:
			ctx.author = g.get_member(ctx.author.id)
			if role in [x.id for x in ctx.author.roles]:
				return True
		else:
			return False

	return commands.check(predicate) #
