import asyncio

import discord
import youtube_dl

from discord.ext import commands

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''


ytdl_format_options = {
	'format': 'bestaudio/best',
	'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
	'restrictfilenames': True,
	'noplaylist': True,
	'nocheckcertificate': True,
	'ignoreerrors': False,
	'logtostderr': False,
	'quiet': True,
	'no_warnings': True,
	'default_search': 'auto',
	'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
	'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
	def __init__(self, source, *, data, volume=0.5):
		super().__init__(source, volume)

		self.data = data

		self.title = data.get('title')
		self.url = data.get('url')

	@classmethod
	async def from_url(cls, url, *, loop=None, stream=False):
		loop = loop or asyncio.get_event_loop()
		data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

		if 'entries' in data:
			# take first item from a playlist
			data = data['entries'][0]

		filename = data['url'] if stream else ytdl.prepare_filename(data)
		return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

def alone_or_admin():
	def pred(ctx):
		if not isinstance(ctx.channel, discord.VoiceChannel):
			return False
		elif ctx.author.guild_permissions.administrator:
			return True
		elif ctx.author.guild_permissions.manage_server:
			return True
		elif ctx.author.guild_permissions.manage_channels:
			return True
		else:
			users = len(ctx.channel.members)
			if ctx.guild.me.voice_client.channel is not None and ctx.guild.me.voice_client.channel == ctx.channel:
				users -= 1  # bot
			if users <= 1:
				return True
			else:  # more then 1 user
				return False
	return commands.check(pred)


class Music(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.playing = {"GUILD_ID": ["URL_1", "URL_2"]}

	@commands.command()
	async def join(self, ctx, *, channel: discord.VoiceChannel = None):
		"""Joins a voice channel"""
		def check():
			x = str(ctx.guild.id)
			if x in self.playing:
				if len(self.playing[x]) > 0:
					return False
				else:  # empty queue
					return True
			else:
				return True
		if ctx.voice_client is not None:
			if ctx.voice_client.is_playing():
				if not ctx.author.guild_permissions.administrator:
					return await ctx.send("Im still playing music!")
		if ctx.voice_client is not None:
			if str(ctx.guild.id) not in self.playing:
				self.playing[str(ctx.guild.id)] = []
			return await ctx.voice_client.move_to(channel)
		if str(ctx.guild.id) not in self.playing:
			self.playing[str(ctx.guild.id)] = []
		await channel.connect()

	async def _play_pool(self, ctx):
		for track in self.playing[str(ctx.guild.id)]:
			try:
				ctx.voice_client.play(track)
				self.playing[str(ctx.guild.id)].remove(track)
			except (Exception, discord.Forbidden) as x:
				await ctx.send(f"Error while playing track: `{str(x)}`\nskipping...")
				if len(self.playing[str(ctx.guild.id)]) == 0:
					return None
				continue
		return

	@commands.command(aliases=['play', 'yt'])
	async def stream(self, ctx, *, url):
		"""Streams from a youtube url"""
		if str(ctx.guild.id) not in self.playing:
			self.playing[str(ctx.guild.id)] = []
		async with ctx.typing():
			player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
			if len(self.playing[str(ctx.guild.id)]) > 0:

		ctx.voice_client.play(player)

		await ctx.send('Now playing: {}'.format(player.title))

	@commands.command()
	@alone_or_admin()
	async def volume(self, ctx, volume: float):
		"""Changes the player's volume"""
		volume = round(volume, 1)
		if volume > 200.00:
			return await ctx.send("Damn that's way to loud! please provide a number below **200.00**.")
		elif volume < 25.00:
			return await ctx.send("You can hear that? Please give me a number above **25.00**.")
		if ctx.voice_client is None:
			return await ctx.send("Im not connected to a voice channel! use `{.prefix}join` first.".format(ctx))

		ctx.voice_client.source.volume = volume
		await ctx.send("Changed volume to {}%".format(volume))

	@commands.command()
	@alone_or_admin()
	async def stop(self, ctx):
		"""Stops and disconnects the bot from voice"""
		await ctx.send("Leaving voice channel and stopping music.")
		await ctx.voice_client.disconnect()

	@stream.before_invoke
	async def ensure_voice(self, ctx):
		if ctx.voice_client is None:
			if ctx.author.voice:
				await ctx.author.voice.channel.connect()
			else:
				await ctx.send("You are not connected to a voice channel.")
				raise commands.CommandError("Author not connected to a voice channel.")
		elif ctx.voice_client.is_playing():
			ctx.voice_client.stop()

def setup(bot):
	bot.add_cog(Music(bot))