#!/usr/bin/env python3

import asyncio  # for async stuff and error exceptions
import base64  # for save states
import json  # json
import random
from datetime import datetime
from sys import argv as cliargs

import discord  # discord library
from discord.ext import commands  # discord library extension to make stuff easier

from libs import (  # libraries to make minesweeper boards, tic tac toe boards, connect four boards, and other stuff respecively
	c4py, extra, minespy, tttpy, unopy
)

if not extra.file_exists("analytics.json"):
	with open("analytics.json","w") as analyticsfile:
		analytics = {}
		for i in ["rps","connectfour","tictactoe","minesweeper","coinflip"]:
			analytics[i] = 0
		analyticsfile.write(json.dumps(analytics))

with open("analytics.json","r") as analyticsfile:
	analytics = json.loads(analyticsfile.read())


# Load prefix from -p or --prefix argument, else it is "j!"
prefix = ""
for parameter in cliargs:
	if parameter == "-p":
		prefix = cliargs[cliargs.index(parameter) + 1]
	elif parameter.startswith("--prefix"):
		x = parameter.split("=")
		prefix = x[1]
prefix = "j!" if prefix == "" else prefix

# Get the tokenfile name from -t or --tokenfile, else it is "tokenfile"
tokenfilename = ""
for parameter in cliargs:
	if parameter == "-t":
		tokenfilename = cliargs[cliargs.index(parameter) + 1]
	elif parameter.startswith("--tokenfile"):
		x = parameter.split("=")
		tokenfilename = x[1]
tokenfilename = "tokenfile" if tokenfilename == "" else tokenfilename

# read token
with open(tokenfilename,"r") as tokenfile:
	token = tokenfile.read()

print(f"prefix:{prefix}")

with open("themes.json", "r") as themesfile:
	themes = json.loads(themesfile.read())

client = commands.Bot(command_prefix=prefix,activity=discord.Game("starting up..."),help_command=extra.MyHelpCommand())
repomsg = discord.Embed(title="Repo",description="https://github.com/jackbotgames/jackbot")
log_channel = None
bug_channel = None
suggestion_channel = None

# print message when bot turns on and also print every guild that its in
@client.event
async def on_ready():
	print(f"logged in as {client.user}")
	print(f"https://discord.com/oauth2/authorize?client_id={client.user.id}&permissions=8192&scope=bot")
	for guild in client.guilds:
		print(f"In guild: {guild.name}")
	print(f"In {len(client.guilds)} guilds")
	global log_channel, bug_channel, suggestion_channel, t0
	log_channel = client.get_channel(784583344188817428)
	bug_channel = client.get_channel(775770636353011752)
	suggestion_channel = client.get_channel(775770609191616512)
	await log_channel.send("waking up")
	await client.change_presence(activity=discord.Game("games"))
	t0 = datetime.now()

# and also print every time it joins a guild
@client.event
async def on_guild_join(guild):
	print(f"Joined guild: {guild.name}")
	await log_channel.send("joined a guild")

class Games(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self._last_member = None
	
	@commands.command(aliases=["ms"],brief="generate minesweeper board")
	async def minesweeper(self, ctx, length: int = 6, width: int = 6, mines: int = 7):
		global analytics
		analytics["minesweeper"] += 1
		extra.update_analytics(analytics)
		await client.change_presence(activity=discord.Game("minesweeper"))
		if length * width > 196:
			await ctx.send(embed=discord.Embed(title="Error",description="Board too large. Try something smaller."))
			return
		if mines >= (length * width):
			mines = (length * width) - 1
		gridstr = minespy.generategrid(length,width,mines)
		while "0" in gridstr or "1" in gridstr or "2" in gridstr or "3" in gridstr or "4" in gridstr or "5" in gridstr or "6" in gridstr or "7" in gridstr or "7" in gridstr or "B" in gridstr: # stole this from stackoverflow
			gridstr = gridstr.replace("0","||:zero:||")
			gridstr = gridstr.replace("1","||:one:||")
			gridstr = gridstr.replace("2","||:two:||")
			gridstr = gridstr.replace("3","||:three:||")
			gridstr = gridstr.replace("4","||:four:||")
			gridstr = gridstr.replace("5","||:five:||")
			gridstr = gridstr.replace("6","||:six:||")
			gridstr = gridstr.replace("7","||:seven:||")
			gridstr = gridstr.replace("8","||:eight:||")
			gridstr = gridstr.replace("B","||:boom:||")
		gridstr = extra.replacenth(gridstr,"||:zero:||",":zero:",random.randint(0,gridstr.count("||:zero:||")))
		embed = discord.Embed(title=f"{length}x{width} with {mines} mines",description=gridstr)
		await ctx.send(embed=embed)

	@commands.command(brief="play rock paper scissors with someone")
	async def rps(self, ctx,member):
		global analytics
		analytics["rps"] += 1
		extra.update_analytics(analytics)
		await client.change_presence(activity=discord.Game("rock paper scissors"))
		otherguy = ctx.message.mentions[0]
		if ctx.author.dm_channel == None:
			await ctx.author.create_dm()
		if otherguy.dm_channel == None:
			await otherguy.create_dm()
		authormsg = await ctx.author.dm_channel.send("Rock, paper, or scissors?")
		otherguymsg = await otherguy.dm_channel.send("Rock, paper, or scissors?")
		for i in u"\U0001f5ff\U0001f4f0\u2702": # rock/paper/scissors
			await authormsg.add_reaction(i)
			await otherguymsg.add_reaction(i)
		def check(reaction,user):
			return (user.id == ctx.author.id or user.id == otherguy.id) and (reaction.message == authormsg or reaction.message == otherguymsg)
		players = []
		winner = None
		while len(players) < 2:
			try:
				reaction,user = await client.wait_for("reaction_add", timeout=60.0, check=check)
			except asyncio.exceptions.TimeoutError:
				await ctx.send("Game closed due to inactivity.")
				return
			stop = False
			for i in players:
				if user in i:
					stop = True
			if stop:
				continue
			players.append([reaction,user])
		if str(players[0][0].emoji) == u"\U0001f5ff" and str(players[1][0].emoji) == u"\U0001f4f0": # rock < paper
			winner = players[1][1].name
		elif str(players[0][0].emoji) == u"\U0001f4f0" and str(players[1][0].emoji) == u"\U0001f5ff": # paper > rock
			winner = players[0][1].name
		elif str(players[0][0].emoji) == u"\u2702" and str(players[1][0].emoji) == u"\U0001f4f0":     # paper < scissors
			winner = players[0][1].name
		elif str(players[0][0].emoji) == u"\U0001f4f0" and str(players[1][0].emoji) == u"\u2702":     # scissors > paper
			winner = players[1][1].name
		elif str(players[0][0].emoji) == u"\u2702" and str(players[1][0].emoji) == u"\U0001f5ff":     # scissors < rock
			winner = players[1][1].name
		elif str(players[0][0].emoji) == u"\U0001f5ff" and str(players[1][0].emoji) == u"\u2702":     # rock > scissors
			winner = players[0][1].name
		else:
			description = f"{players[0][0].emoji}   v   {players[1][0].emoji}\n\nIts a tie!"
		if winner != None:
			description = f"{players[0][0].emoji}   v   {players[1][0].emoji}\n\n{winner} wins!"
		title = f"{players[0][1].name} v {players[1][1].name}"
		game_embed = discord.Embed(title=title,description=description)
		await ctx.send(embed=game_embed)
		await otherguy.dm_channel.send(embed=game_embed)
		await ctx.author.dm_channel.send(embed=game_embed)

	@commands.command(aliases=["ttt"],brief="play tic tac toe with someone",description="play tic tac toe with someone.\nthe controls are WASD, meaning that its: ```\nAW W WD\nA  .  D\nAS S SD```")
	async def tictactoe(self, ctx,member,save = None):
		global analytics
		analytics["tictactoe"] += 1
		await client.change_presence(activity=discord.Game("tic tac toe"))
		extra.update_analytics(analytics)
		valid_t_movements = ["w", "a", "s", "d", "wa", "wd", "sa", "sd", ".", "q", "aw", "dw", "as", "sd"]
		opponent = ctx.message.mentions[0]
		await ctx.send(f"playing tic tac toe with {opponent.display_name if opponent.id != 775408192242974726 else 'an AI'}")
		if save is not None:
			base = base64.b64decode(save.encode()).decode("utf-8").split("|")
			g = base[0]
			moves = int(base[1])
		else:
			g = tttpy.generategrid()
			moves = 1
		gs = g
		gs = gs.replace("X",":regional_indicator_x:")
		gs = gs.replace("O",":zero:")
		for i in gs:
			if str(i) in "123456789":
				gs = gs.replace(i,":blue_square:")
		title = f"Tic Tac Toe: *{ctx.author.display_name}*:regional_indicator_x: vs {opponent.display_name}:zero:" if moves % 2 == 1 else f"Connect 4: {ctx.author.display_name}:regional_indicator_x: vs *{opponent.display_name}*:zero:"
		msgembed = discord.Embed(title=title)
		msgembed.description = gs
		savestate = base64.b64encode(f"{g}|{moves}".encode()).decode("utf-8")
		msgembed.set_footer(text=savestate)
		bmsg = await ctx.send(embed=msgembed)
		def check(message):
			user = message.author
			return ((user == opponent if moves % 2 == 0 else user == ctx.author) and (message.content in valid_t_movements or message.content)) or message.content in ["q","r"]
		while moves <= 9:
			try:
				m = await client.wait_for("message",timeout=60.0,check=check)
			except asyncio.exceptions.TimeoutError:
				await ctx.send("Game closed due to inactivity.")
				return
			c = m.content.lower()
			if c in ["as","ds","aw","dw"]:
				c = c[::-1]
			og = g
			char = "X" if moves % 2 == 1 else "O"
			if c == "q":
				await ctx.send("Game closed.")
				return
			if c == "r":
				title = f"Tic Tac Toe: *{ctx.author.display_name}*:regional_indicator_x: vs {opponent.display_name}:zero:" if moves % 2 == 1 else f"Connect 4: {ctx.author.display_name}:regional_indicator_x: vs *{opponent.display_name}*:zero:"
				msgembed = discord.Embed(title=title)
				msgembed.description = gs
				bmsg = await ctx.send(embed=msgembed)
				savestate = base64.b64encode(f"{g}|{moves}".encode()).decode("utf-8")
				msgembed.set_footer(text=savestate)
				continue
			if c == "wa":
				g = g.replace("1",char)
			elif c == "w":
				g = g.replace("2",char)
			elif c == "wd":
				g = g.replace("3",char)
			elif c == "a":
				g = g.replace("4",char)
			elif c == ".":
				g = g.replace("5",char)
			elif c == "d":
				g = g.replace("6",char)
			elif c == "sa":
				g = g.replace("7",char)
			elif c == "s":
				g = g.replace("8",char)
			elif c == "sd":
				g = g.replace("9",char)
			else:
				continue
			if og != g:
				moves += 1
			try:
				await m.delete()
			except discord.Forbidden:
				pass
			gs = g
			gs = gs.replace("X",":regional_indicator_x:")
			gs = gs.replace("O",":zero:")
			for i in gs:
				if str(i) in "123456789":
					gs = gs.replace(i,":blue_square:")
			title = f"Tic Tac Toe: *{ctx.author.display_name}*:regional_indicator_x: vs {opponent.display_name}:zero:" if moves % 2 == 1 else f"Connect 4: {ctx.author.display_name}:regional_indicator_x: vs *{opponent.display_name}*:zero:"
			msgembed = discord.Embed(title=title)
			msgembed.description = gs
			savestate = base64.b64encode(f"{g}|{moves}".encode()).decode("utf-8")
			msgembed.set_footer(text=savestate)
			await bmsg.edit(embed=msgembed)
			glist = []
			for i in g.split("\n"):
				if i == "":
					continue
				gltmp = []
				for j in i:
					gltmp.append(j)
				glist.append(gltmp)
			if tttpy.checkWin(glist):
				winner = ctx.author.display_name if moves % 2 == 0 else opponent.display_name
				await ctx.send(f"{winner} has won!")
				return
			elif moves > 9:
				await ctx.send("Nobody won, the game is tied.")
				return


	@commands.command(aliases=["c4"],brief="play connect four with someone",description="play connect four with someone.\n controls are the numbers 1 - 7, and the tile drops on whichever column you type in.\ncodes are:\n{0}".format('\n'.join(extra.list_layouts("c4layouts.json"))))
	async def connectfour(self, ctx,member,save = None):
		tiles_list = themes[random.choice(list(themes))]
		global analytics
		analytics["connectfour"] += 1
		await client.change_presence(activity=discord.Game("connect 4"))
		extra.update_analytics(analytics)
		valid_c_movements = [ str(i) for i in range(1,8) ]; valid_c_movements.append("q"); valid_c_movements.append("r")
		opponent = ctx.message.mentions[0]
		with open("c4layouts.json", "r") as c4layoutsfile:
			c4layouts = json.loads(c4layoutsfile.read())
		await ctx.send(f"playing connect 4 with {opponent.display_name}")
		if (save in c4layouts):
			save = c4layouts[save]
		if save is not None:
			base = base64.b64decode(save.encode()).decode("utf-8").split("|")
			g = json.loads(base[0].replace("'",'"'))
			moves = int(base[1])
		else:
			g = ["       \n" for _ in range(7)]
			moves = 1
			base = None
		if base is not None:
			pass
		gridstr = "".join(g[::-1])
		theme = random.choice(list(themes))
		tiles_list = dict(themes[theme])
		nums_list = "".join(tiles_list["nums"])
		gridstr += nums_list
		tiles_list.pop("nums")
		for tile in tiles_list: gridstr = gridstr.replace(tile,tiles_list[tile])
		title = f"Connect 4: *{ctx.author.display_name}*{tiles_list['X']} vs {opponent.display_name}{tiles_list['O']}" if moves % 2 == 1 else f"Connect 4: {ctx.author.display_name}{tiles_list['X']} vs *{opponent.display_name}*{tiles_list['O']}"
		if len(gridstr) > 2048:
			await ctx.send("The grid is too big!")
			return
		msgembed = discord.Embed(title=title)
		msgembed.description = gridstr
		savestate = base64.b64encode(f"{json.dumps(g)}|{moves}".encode()).decode("utf-8")
		msgembed.set_footer(text=savestate)
		bmsg = await ctx.send(embed=msgembed)
		while moves <= 42:
			def check(message):
				user = message.author
				return ((user == opponent if moves % 2 == 0 else user == ctx.author) and (message.content in valid_c_movements or message.content)) or (message.content in ["q","r"] and (user == opponent or user == ctx.author))
			m = await client.wait_for("message",timeout=None,check=check)
			c = m.content
			if c not in valid_c_movements:
				continue
			if c == "q":
				await ctx.send("game ended")
				return
			elif c == "r":
				title = f"Connect 4: *{ctx.author.display_name}*{tiles_list['X']} vs {opponent.display_name}{tiles_list['O']}" if moves % 2 == 1 else f"Connect 4: {ctx.author.display_name}{tiles_list['X']} vs *{opponent.display_name}*{tiles_list['O']}"
				msgembed = discord.Embed(title=title)
				msgembed.description = gridstr
				savestate = base64.b64encode(f"{json.dumps(g)}|{moves}".encode()).decode("utf-8")
				msgembed.set_footer(text=savestate)
				bmsg = await ctx.send(embed=msgembed)
				continue
			bg = list(g)
			if c in "1234567":
				for y in g:
					# and not (y == g[0] and y[int(c) - 1] in ["X","O"])
					if not y[int(c) - 1] == " ": continue
					t = list(y)
					t[int(c) - 1] = "X" if moves % 2 == 1 else "O"
					g[g.index(y)] = "".join(t)
					break
				moves += 1 if bg != g else 0
			else:
				continue
			gridstr = "".join(g[::-1])
			for tile in tiles_list: gridstr = gridstr.replace(tile,tiles_list[tile])
			gridstr += nums_list
			title = f"Connect 4: *{ctx.author.display_name}*{tiles_list['X']} vs {opponent.display_name}{tiles_list['O']}" if moves % 2 == 1 else f"Connect 4: {ctx.author.display_name}{tiles_list['X']} vs *{opponent.display_name}*{tiles_list['O']}"
			msgembed = discord.Embed(title=title)
			msgembed.description = gridstr
			savestate = base64.b64encode(f"{json.dumps(g)}|{moves}".encode()).decode("utf-8")
			msgembed.set_footer(text=savestate)
			await bmsg.edit(embed=msgembed)
			await m.delete()
			glist = []
			for i in g:
				if i == "\n":
					continue
				gltmp = []
				for j in i:
					gltmp.append(j)
				glist.append(gltmp)
			if c4py.check_win(glist,"X") or c4py.check_win(glist,"O"):
				winner = ctx.author.display_name if moves % 2 == 0 else opponent.display_name
				await ctx.send(f"{winner} has won!")
				return
			elif moves > 42:
				await ctx.send("Nobody won, the game is tied. How did you manage to do that in connect 4?")
				return
	
	@commands.command(brief="play uno")
	async def uno(self, ctx, opponent):
		opponent = ctx.message.mentions[0]
		await ctx.send(f"playing uno with {opponent.display_name}")
		p1cards = []
		p2cards = []
		for i in range(7):
			p1cards.append(unopy.generate_card())
			p2cards.append(unopy.generate_card())
		await ctx.send("player 1's cards are:\n{0}\nplayer 2's card are:\n{1}\n".format('\n'.join(p1cards),'\n'.join(p2cards)))

class Fun(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self._last_member = None

	@commands.command(brief="roll a dice")
	async def roll(self, ctx, number_of_dice: int, number_of_sides: int):
		dice = [
			str(random.choice(range(1, number_of_sides + 1)))
			for _ in range(number_of_dice)
		]
		await ctx.send(", ".join(dice))

	@commands.command(brief="flip a coin")
	async def coinflip(self, ctx):
		global analytics
		analytics["coinflip"] += 1
		extra.update_analytics(analytics)
		await ctx.send(f"It landed on {'heads' if random.choice([0,1]) == 0 else 'tails'}!")

	@commands.command(brief="show jack")
	async def jack(self,ctx):
		await ctx.send("<:jack1:784513836375212052><:jack2:784513836408504360><:jack3:784513836321079326>\n<:jack4:784513836442189884><:jack5:784513836626477056><:jack6:784513836832522291>\n<:jack7:784513836660031518><:jack8:784513836865814588><:jack9:784513836434325535>")

@client.command(brief="show repo")
async def repo(ctx):
	await ctx.send(embed=repomsg)

@client.command(brief="give link to support server")
async def invite(ctx):
	await ctx.send("join our support server for support and teasers into new features :)\nhttps://discord.gg/4pUj8vNFXY")

@client.command(brief="send bug report to bugs channel in support discord")
async def bugreport(ctx,*report):
	if ctx.guild.id == bug_channel.guild.id:
		return
	if report == ():
		await ctx.send("Provide a report please.")
		return
	txt = " ".join(report)
	guild = "Jackbot's DMs" if ctx.guild is None else ctx.guild.name
	await bug_channel.send(f"**{ctx.author.display_name}** from **{guild}**:\n{txt}",files=await extra.attachments_to_files(ctx.message.attachments))
	await log_channel.send("received a bug report")
	await ctx.message.add_reaction(b'\xe2\x9c\x85'.decode("utf-8"))

@client.command(brief="send suggestion to feature requests channel in support discord")
async def suggestion(ctx,*report):
	if ctx.guild.id == suggestion_channel.guild.id:
		return
	if report == ():
		await ctx.send("Provide a suggestion please.")
		return
	txt = " ".join(report)
	guild = "Jackbot's DMs" if ctx.guild is None else ctx.guild.name
	await suggestion_channel.send(f"**{ctx.author.display_name}** from **{guild}**:\n{txt}",files=await extra.attachments_to_files(ctx.message.attachments))
	await log_channel.send("received a suggestion")
	await ctx.message.add_reaction(b'\xe2\x9c\x85'.decode("utf-8"))


@client.command(brief="show statistics, including usage and amount of servers")
async def stats(ctx):
	global analytics
	embed = discord.Embed(title="Analytics")
	embed.add_field(name="Servers",value=f"{client.user.name} is in {len(client.guilds)} servers.")
	str_usage_stats = ""
	for cmd in analytics:
		str_usage_stats += f"{cmd}: {analytics[cmd]}\n"
	embed.add_field(name="Usage stats",value=str_usage_stats)
	embed.add_field(name="Uptime",value=str(datetime.now() - t0).split(".")[0])
	await ctx.send(embed=embed)

@client.command(brief="show latency")
async def ping(ctx):
	await ctx.send(f"Pong! {int(client.latency * 1000)}ms")

client.add_cog(Games(client))
client.add_cog(Fun(client))
client.run(token)

# vim: noet ci pi sts=0 sw=4 ts=4: