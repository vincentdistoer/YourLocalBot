import discord
import typing
from discord.ext import commands


class NotFound(Exception):
	pass


class InvalidFramework(Exception):
	pass


class HasNoAccount(Exception):
	pass


class GetError(Exception):
	def __init__(self, *, code: int, reason: str):
		self.code = code
		self.reason = reason

	def __str__(self):
		return f"error code 000{self.code}: {self.reason}"

	def __int__(self):
		return self.code

### audit


class AuditFail(Exception):
	pass


class InvalidAuditData(AuditFail):
	def __init__(self, invalid_data):
		self.invalid_data = invalid_data

	def __str__(self):
		return f'InvalidAuditData: `{self.invalid_data}` (type {type(self.invalid_data)} passed and could not be accepted.'

	def __int__(self):
		raise TypeError("Cant convert type `InvalidAuditData` to int.")


class NotEnoughData(InvalidAuditData):
	def __init__(self):
		pass

	def __str__(self):
		return 'Not enough data was passed to audit'


class AutoRoleFail(Exception):
	def __init__(self, ctx: commands.Context, role: discord.Role, info: str):
		self.ctx = ctx
		self.role = role
		self.info = info

	def __str__(self):
		return f'{self.ctx.guild} on {self.role.name}: {self.info}'


class RoleNotFound(AutoRoleFail):
	def __init__(self,  ctx: commands.Context, role_id: int):
		self.ctx = ctx
		self.role = role_id

	def __str__(self):
		roles = [role.id for role in self.ctx.guild.roles]
		_roles = "'" + "', '".join(roles) + "'"
		return f'{self.ctx.guild.name}: {self.role} not found in {_roles}.'
