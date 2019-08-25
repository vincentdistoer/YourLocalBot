import discord
from typing import Union, Optional 
# for all misc things
def support_guild(ctx):
    return discord.utils.get(ctx.bot.guilds, id=486910899756728320)

class get_user:
    @staticmethod
    def by_name(ctx, name:str):
        """Get someone via name"""
        return discord.utils.find(ctx.bot.users, name=name)
    @staticmethod
    def by_id(ctx, id: int):
        return discord.utils.get(ctx.bot.users, id=id)
class convert:
  @staticmethod
  def to_int(stuff):
    rett = []
    for x in list(stuff):
      try:
        rett.append(int(x))
      except:
        pass
    return ret
  @staticmethod
  def to_str(stuff):
    return str(stuff)

class get:
    def __init__(self, ctx):
        self.bot = ctx.bot
    def fuzzy_guild(ctx, name=typing.Optional[str], id=typing.Optional[int]):
        found = []
        for guild in self.bot.guilds:
            if name is not None:
                if name.lower in guild.name:
                    found.append(guild)
            elif id is not None:
                if guild.id == id:
                    found.append(guild)
        return found if len(found) > 0 else None
