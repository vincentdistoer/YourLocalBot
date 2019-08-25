import discord, json, traceback, asyncio
from discord.ext import commands

class json_mngr:
    class IdNotFound(Exception):
        pass

    def __init__(self, hi: str=None):
        self.hi = 'this doesnt do anything, just to keep backwards compat'

    @staticmethod
    def handle_modify(fp: str, newdata: dict, indent=2, *, backup: bool=False):
        if backup:
            with open(fp, 'r') as back:
                hackup=json.load(back)
        try:
            with open(fp, 'w') as alafile:
                try:
                    json.dump(newdata, alafile, indent=indent)
                    return json.load(alafile)
                except:
                    json.dump(hackup, alafile, indent=indent)
                    raise
        except:
            raise

    @staticmethod
    def read(fp):
        try:
            with open(fp, 'r') as alafile:
                try:
                    z = json.load(alafile)
                    return z
                except:
                    raise
        except:
            raise

    @staticmethod
    async def find(fp, *, in_key: str, thing):
        with open(fp, 'r') as tofind:
            data = json.load(tofind)
            if data:
                if in_key in data.keys():
                    if thing in data[in_key].keys():
                        return data[in_key][thing]
                else:
                    raise json_mngr.IdNotFound(f"{in_key} not found in {data}")

    @staticmethod
    def format(fp: str, *, data: dict, indents: int = 0, create: bool = True):
        """
        format a file, ready for modifying
        WARNING: THIS WILL OVERWRITE ANY EXISTING DATA
        :param fp:
        :param data:
        :param indents:
        :return:
        """
        if create:
            mode = 'w+'
        else:
            mode = 'w'
        with open(fp, mode) as file:
            file.write('{}')
            json.dump(data, file, indent=indents)
        return


class Config(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.group(invoke_without_command=True)
    async def config(self, ctx):
        """
        configuration management.
        please read subcommands
        """
        await ctx.invoke(self.bot.get_command('help'), command=ctx.command.name)

    @config.command()
    @commands.has_permissions(manage_channels=True)
    async def bumpchannel(self, ctx, new: discord.TextChannel=None):
        """
        set your own bump channel! leave <new> blank to see your current channel.
        """
        if not new:
            current = json_mngr().read('./data/config.json')
            if str(ctx.guild.id) not in current['bumpchannels'].keys():
                return await ctx.send("You haven't set a custom bump channel yet!")
            return await ctx.send(f"Your custom bump channel is <#{current['bumpchannels'][str(ctx.guild.id)]}>.")
        else:
            current = json_mngr().read('./data/config.json')
            print(current)
            i = str(ctx.guild.id)
            print(i)
            current['bumpchannels'][i] = new.id
            json_mngr().handle_modify('./data/config.json', current, backup=True)
            await ctx.send(f"Set custom bump channel to {new.mention}. sending a test message now.")
            await new.send(embed=discord.Embed(title="Test complete."))
    
    @config.command()
    @commands.has_permissions(manage_guild=True)
    async def modlog(self, ctx, new: discord.TextChannel=None):
        """
        set your own modlog channel! leave <new> blank to see your current channel.
        """
        if not new:
            current = json_mngr().read('./data/config.json')
            if str(ctx.guild.id) not in current['modlogs'].keys():
                return await ctx.send("You haven't set a custom modlog channel yet!")
            return await ctx.send(f"Your custom modlog channel is <#{current['bumpchannels'][str(ctx.guild.id)]}>.")
        else:
            current = json_mngr().read('./data/config.json')
            i = str(ctx.guild.id)
            current['modlogs'][i] = new.id
            json_mngr().handle_modify('./data/config.json', current, backup=True)
            await ctx.send(f"Set custom log channel to {new.mention}. sending a test message now.")
            await new.send(embed=discord.Embed(title="Test complete."))

    @config.command()
    @commands.has_permissions(manage_roles=True)
    async def mutedrole(self, ctx, new:discord.Role=None):
        """
        set your own muted role, used in `y!mute`! leave <new> blank to see your current role.
        """
        if not new:
            current = json_mngr().read('./data/config.json')
            if str(ctx.guild.id) not in current['mutedroles'].keys():
                return await ctx.send("You haven't set a custom role yet!\n*a new one will automatically be created if "
                                      "you mute without this being set.*")
            return await ctx.send(f"Your custom modlog channel is <#{current['bumpchannels'][str(ctx.guild.id)]}>.")
        else:
            current = json_mngr().read('./data/config.json')
            i = str(ctx.guild.id)
            current['mutedroles'][i] = new.id
            json_mngr().handle_modify('./data/config.json', current, backup=True)
            await ctx.send(f"Custom mute role set to {new.name}. try it out!")

    @config.command(name='reset')
    async def _reset(self, ctx):
        """
        Reset all settings back to their defaults (empty)
        """
        g = str(ctx.guild.id)
        if ctx.author != ctx.guild.owner:
            return await ctx.send("You must be the guild owner to do this.")
        data = json_mngr().read('./data/config.json')
        if g not in data['bumpchannels'].keys() and g not in data['modlogs']:
            return await ctx.send("You have no data to reset!")
        msg = await ctx.send("Resetting data...")
        if g in data['bumpchannels'].keys():
            del data['bumpchannels'][g]
        if g in data['modlogs'].keys():
            del data['modlogs'][g]
        if g in data['mutedrole'].keys():
            del data['mutedrole'][g]
        json_mngr().handle_modify('./data/config.json', data)
        await msg.edit(content="Successfully reset all of your data.")


def setup(bot):
    bot.add_cog(Config(bot))
