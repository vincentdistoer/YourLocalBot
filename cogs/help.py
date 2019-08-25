import discord, typing, random, datetime

from discord.ext import commands


class BackupHelp(commands.DefaultHelpCommand):
    pass


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.name = 'help'
        self.backup = {'minimal': True}

    def cog_unload(self):
        self.bot.help_command = commands.MinimalHelpCommand() if self.backup['minimal'] else commands.DefaultHelpCommand()

    def get_cog(self, s: str):
        for cog in self.bot.cogs:
            if cog.lower() == s.lower():
                return cog
        else:
            return None

    async def embed_it(self, ctx: typing.Optional[commands.Context], *, comma: str=None):
        if comma is not None:
            command = self.bot.get_command(comma)
            if command is None:
                cog = self.get_cog(comma)
                if not cog:
                    cog = self.bot.get_cog(cog)
                if cog is None:
                    return discord.Embed(title="Command not found!", description="did you make a typo?",
                                         color=discord.Color.red(), timestamp=datetime.datetime.utcnow())
                else:
                    if not isinstance(cog, commands.Cog):
                        raise TypeError
                    cr = []
                    e = discord.Embed(title=f"{cog.qualified_name}:", description="",
                                      color=discord.Color.dark_blue())
                    for cmd in cog.get_commands():
                        try:
                            x = await cmd.can_run(ctx)
                            if x:
                                cr.append((cmd.name, cmd.short_doc))
                        except:
                            continue
                    for name, breif in cr:
                        e.description += f'{name}: {breif}\n'
                    return e
            else:
                args = command.signature
                e = discord.Embed(
                    title=f"{command.cog_name} -> {command.qualified_name.replace(' ', ' -> ')}:",
                    description=command.help,
                    color=discord.Color.blue() if not command.hidden else discord.Color.greyple()
                )
                e.add_field(name="Arguments:", value="`{0}{1} {2}`"
                                                     "".format(ctx.prefix, command.qualified_name,
                                                               args), inline=False)
                if len(command.aliases) > 0:
                    e.add_field(name="Alias(es):", value=f"`{'`, `'.join(command.aliases)}`", inline=False)
                if command.parent is not None:
                    e.add_field(name="Parent command:", value=command.parent, inline=False)
                if isinstance(command, commands.Group):
                    resol = []
                    for cmd in list(command.commands):
                        resol.append(cmd.name)
                    if len(resol) != 0:
                        e.add_field(name="Subcommands:", value=f"`{'`, `'.join(resol)}`", inline=False)
                e.set_footer(text="\n*things wrapped in: `< >` = required | `[ ]` = optional | "
                                  "`[ ]...` = list of items, required*")
                try:
                    x = await command.can_run(ctx)
                    if x:
                        pass
                    else:
                        e.color = discord.Color.purple()
                except:
                    e.color = discord.Color.purple()
                return e

        # all help
        cogs = self.bot.cogs
        formatted = {}
        for cog in cogs:
            cog = self.bot.get_cog(cog)
            cmds = []
            for com in cog.get_commands():
                if com.hidden:
                    continue
                try:
                    if await com.can_run(ctx):
                        cmds.append(com)
                        continue
                    else:
                        continue
                except:
                    continue
            fmt_fin = []
            for x in cmds:
                fmt_fin.append(x.name)
            fmt_fin = ' ~ '.join(fmt_fin)
            formatted[cog.qualified_name] = fmt_fin
        return formatted

    @commands.group(aliases=['newhelp', 'nh', '?'], invoke_without_command=True)
    async def help(self, ctx, *, command: str = None):
        """
        The new, embedded, beta help command!
        to get a subcommand, do `help [command parent] [subcommand]`
        """
        if command is not None:
            embed = await self.embed_it(ctx, comma=command)
            return await ctx.send(embed=embed)
        e = discord.Embed(title="YourLocalBot help!", description="This embed will close in 2m 30s after invoke.", color=discord.Color.blue(),
                          timestamp=datetime.datetime.utcnow(), url="https://invite.gg/ebot")
        to = await self.embed_it(ctx)
        if len(list(to)) > 25:
            return await ctx.send("Sorry, but the help command is too long to display.")
        for cog in list(to):
            if len(to[cog]) > 1024:
                value = f"{cog} has too many commands, too large to display."
            else:
                value = to[cog]
            if len(value) == 0:
                # await ctx.send(f"{cog.qualified_name} has no value!")
                continue
            # await ctx.send(value)
            e.add_field(name=f"{cog}:", value=value)
        try:
            return await ctx.send(embed=e, delete_after=150)
        except discord.Forbidden as e:
            if not ctx.guild.me.guild_permissions.embed_links:
                await ctx.send("***Critical error: I lack __embed links__ permissions. If I do not have this permission"
                               " errors will not notify my developer, and most of my commands will not work! Please "
                               "give me this permission ASAP!***")
            else:
                await ctx.send(f"hmm. Seems I'm missing permissions, but don't know which ones. `{e}`")
        except discord.HTTPException as e:
            await ctx.send("The help embed failed to send; please notify a developer of the following error: `{}`".format(
            e))

    @staticmethod
    async def _format(top_guild, las_guild):
        words = ['http', 'https', '://', '.gg', '.com', 'https://invite.gg']
        top_name = top_guild.name
        las_name = las_guild.name
        for word in words:
            top_name.replace(word, '#'*len(word))
            las_name.replace(word, '#'*len(word))
        top_name = discord.utils.escape_markdown(top_name)
        las_name = discord.utils.escape_markdown(las_name)
        return discord.utils.escape_mentions(top_name), discord.utils.escape_mentions(las_name)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def largestguild(self, ctx):
        """finds my largest guild."""
        top_guild = sorted(ctx.bot.guilds, key=lambda _guild: _guild.member_count, reverse=True)[0]
        las_guild = sorted(ctx.bot.guilds, key=lambda _guild: _guild.member_count, reverse=False)[0]
        topname, botname = await self._format(top_guild, las_guild)
        fmt = f'Largest guild: {topname} with **`{top_guild.member_count}`** members!\n'
        fmt += f'Smallest guild: {botname} with **`{las_guild.member_count}`** members!'
        return await ctx.send(fmt)


def setup(bot):
    bot.remove_command("help")
    bot.add_cog(Help(bot))
