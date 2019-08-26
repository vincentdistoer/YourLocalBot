# YourLocalBot!
### known as one of the greatest dragdev bots ever!

## A few opening notes...
So i made the bot open source as per the tradition of [DragDev Studios](https://dragdev.xyz). I never expected this many people to want the code for it so that they can use their own, or even learn from it.\
First of all, THE TOKEN IS NOT A REAL TOKEN! if you remove the `.`s from it and decode it [here](https://www.base64decode.org/), you will kinda get a funny message.\
Second, im fluent in spaghetti code. if thats an issue for you, i wouldn't recommend this.\
Third, i don't understand half of this. i just write it and pray that it works. This code spans back from the discord.py early rewrite alpha builds, and was last updated on to discord.py `1.2.3`.\
Finally: if you decide to run your own version of this bot ([see me](https://github.com/dragdev/YourLocalBot#running-your-own)), i request that you give me some sort of credit somewhere in the bot. even if its as simple as putting the [website url (https://dragdev.xyz)](https://dragdev.xyz). thanks.\
\
**IF YOU DONT KNOW BASIC PYTHON I WILL NOT HELP WITH ANY ERRORS YOU HAVE. I WILL ONLY HELP WITH ACTUAL BUGS.**

## Running your own
Now many people want to run their own local bot. well, its not as easy as downloading, unzipping and running. z
[The bot uses a lot of these custom checks](https://github.com/dragdev/YourLocalBot/blob/master/utils/checks.py), which are hardcoded with IDs to ensure the saftey.\
also in the [Boot file], the owner ID is set to MY ID. this means if i find your instance, and you havent changed that ID, i could do anything with your instance. not that i would. all you need to do, is replace the ID after `owner_id=` to YOUR ID. note it cant have "quotes" which makes it a string.
as for the checks file you will want to find where it says
```python
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
```
you will want to replace the IDs to give yourself access/remove the above users access
*note that whatever comes after the : doesnt matter, the bot doesnt check that.*

### actually setting up
*[There is a video tutorial here](https://www.youtube.com/watch?v=x9NOJ2o7yXY&feature=youtu.be)*
0) go to requirements.txt and pip install everything in it
1) click `clone or download`, `download ZIP`
2) wait for it to download if ur internet a snail
3) unzip it and copy the files inside, or rename the folder.
4) open command prompt/console
5) cd to the downloaded and unzipped location
6) if you are on windows, run `py makeitwork.py`, else run `python3 makeitwork.py`.\
**Notes:**\
This checklist only covers RUNNING the bot. you need to change the token n stuff yourself.
