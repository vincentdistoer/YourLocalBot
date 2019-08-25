"""all misc cmds"""
import discord, datetime, asyncio
from random import choice, randint
from typing import Union, Optional
from utils.formatting import Humanreadable
from discord.ext import commands


class MiscCmds(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_update(self, before, after): 
        if before.id == 499262934715727872 and before.status != discord.Status.offline:
            if after.status == discord.Status.offline:
                guild = discord.utils.get(self.bot.guilds, id=480959345601937410)
                sc = discord.utils.get(guild.text_channels, name="chromebot-status")
                await guild.owner.send('***CHROMEBOT HAS DIED ***')
                if sc is not None:
                    await sc.send('Automated message: chromebot is down.')

    @commands.command()
    async def randomemoji(self, ctx):
        """get a random emoji!

        usage: y!randomemoji
        example: y!randomemoji"""
        try:
            return await ctx.send(choice(self.bot.emojis))
        except discord.HTTPException:
            return await ctx.send("An error occurred while retrieving an emoji. try again later.")

    @commands.command(aliases=['ei', 'emojii', 'einfo'])
    async def emojiinfo(self, ctx, emoji: Optional[discord.Emoji], emoji_fallback: Union[str, int] = None):
        """Get info on any emoji!
        if the emoji converter fails to convert it will attempt to find the emoji itself.

        usage: y!emoji <emoji name/id>
        examples:
        • y!emoji loading
        • y!emoji
        """
        if emoji is not None:
            name = emoji.name
            id = emoji.id
            url = str(emoji.url)
            ani = emoji.animated
            crea = Humanreadable.dynamic_time(emoji.created_at)
            guild = emoji.guild
            e = discord.Embed(title=name, url=url, timestamp=emoji.created_at, color=ctx.author.color)
            e.description = f"**Name:** {name}\n**ID:** {id}\n**url:** {url}\n**Animated?:** {ani}\n" \
                            f"**Created:** {crea}\n**Guild:** {guild.name}"
            e.set_thumbnail(url=url)
            await ctx.send(embed=e)  # 1
        else:
            if isinstance(emoji_fallback, int):  # this makes my life so much easier.
                emoji = await self.bot.fetch_emoji(emoji_fallback)
                name = emoji.name
                id = emoji.id
                url = str(emoji.url)
                ani = emoji.animated
                crea = Humanreadable.dynamic_time(emoji.created_at)
                author = emoji.user
                e = discord.Embed(title=name, url=url, timestamp=emoji.created_at, color=ctx.author.color)
                e.description = f"**Name:** {name}\n**ID:** {id}\n**url:** {url}\n**Animated?:** {ani}\n" \
                    f"**Created:** {crea}\n**Creator:** {author}"
                e.set_thumbnail(url=url)
                e.set_author(name=author.name, icon_url=author.avatar_url)
                await ctx.send(embed=e)  # 2
            else:  # i hate this user
                for emoji in self.bot.emojis:
                    if emoji.name.lower() == emoji_fallback.lower():
                        emoji = emoji
                        break
                    else:
                        continue
                else:
                    for emoji in self.bot.emojis:  # lets do fuzzy
                        if emoji.name.lower().startswith(emoji_fallback.lower()):
                            emoji = emoji
                            break
                        elif emoji_fallback.lower() in emoji.name.lower():
                            emoji = emoji
                            break
                    else:
                        return await ctx.send("Couldn't find the emoji. it most likely doesnt exist.")
                name = emoji.name
                id = emoji.id
                url = str(emoji.url)
                ani = emoji.animated
                crea = Humanreadable.dynamic_time(emoji.created_at)
                guild = emoji.guild
                e = discord.Embed(title=name, url=url, timestamp=emoji.created_at, color=ctx.author.color)
                e.description = f"**Name:** {name}\n**ID:** {id}\n**url:** {url}\n**Animated?:** {ani}\n" \
                    f"**Created:** {crea}\n**Guild:** {guild.name}"
                e.set_thumbnail(url=url)
                await ctx.send(embed=e)  # 3

    @commands.command(name="emojis", aliases=['emojis_for', 'guild_emojis'])
    async def __emojis(self, ctx, the_guild=None):
        """get the emojis of a guild."""
        the_guild = ctx.guild.name if the_guild is None else the_guild
        for g in self.bot.guilds:
            if isinstance(the_guild, int):
                if g.id == the_guild:
                    guild = g
                    break
            else:
                if the_guild.lower() in g.name.lower():  # fuzzy
                    guild = g
                    break
        else:
            return await ctx.send("Guild not found.")
        if len(g.emojis) == 0:
            return await ctx.send("That guild has no emojis!")
        end_emojis = []
        for emoji in guild.emojis:
            end_emojis.append(str(emoji))
        try:
            await ctx.send(' **`--`** '.join(end_emojis))
        except:
            await ctx.send('output too long to display.')
    @commands.command()
    async def gayrate(self, ctx, user: discord.User = None):
        """Accurately tell how gay someone is!"""
        user = user if user is not None else ctx.author
        input = len(user.name)
        middle = input / 5
        end = (middle * 60) / 3
        output = end - 0.3
        if round(output) > 100:
            output = 100
        await ctx.send(f'{user.name} is exactly {output}% gay!')

    async def find_user(self, user: discord.User):
        found = []  # found messages
        for guild in self.bot.guilds:
            #  i would usually just skip the guild if the member isn't in it,
            #  but they might have left and it might have been their last
            #  sent location
            for channel in guild.text_channels:
                try:
                    async for message in channel.history(limit=500):
                        if message.author == user:
                            found.append(message)
                            break
                except (discord.Forbidden, Exception):
                    continue  # skip to next channel.
        newfound = sorted(found, key=lambda message: message.created_at, reverse=True)
        oldest = newfound[-1]
        newest = newfound[0]
        return oldest, newest, newfound

    @commands.command()
    async def find(self, ctx, user: discord.User):
        """Find somebody!"""
        msg = await ctx.send("Finding user and their last message location. Please wait as this can take"
                             " some time.")
        await asyncio.sleep(3)
        async with ctx.message.channel.typing():
            oldest, newest, raw = await self.find_user(user)
            fmt = f"Oldest message: *<{oldest.jump_url}> in {oldest.guild.name}, {oldest.channel.name}.*\n" \
                    f"Newest message: *<{newest.jump_url}> in {newest.guild.name}, {newest.channel.name}.*"
            fmt += f'\n\nLatest message content: {discord.utils.escape_markdown(newest.clean_content)}'
        await msg.edit(content=fmt)


def setup(bot):
    bot.add_cog(MiscCmds(bot))
