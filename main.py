#!/usr/bin/env python3

import json  # json
from datetime import datetime
from sys import argv as cliargs

import discord  # discord library
from discord.ext import commands  # discord library extension to make stuff easier

from libs import extra

from games import Games
from fun import Fun
import traceback
import sys

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
async def on_guild_join(guild:discord.Guild):
	print(f"Joined guild: {guild.name}")
	await log_channel.send("joined a guild")

@client.event
async def on_command_completion(ctx):
	await client.change_presence(activity=discord.Game(ctx.command.name))

@client.event
async def on_command_error(ctx:commands.Context, exception):
	embed = discord.Embed(color=discord.Color.red())
	if type(exception) is commands.errors.MissingRequiredArgument:
		embed.title = "You forgot an argument"
		embed.description = f"The syntax to `{client.command_prefix}{ctx.command.name}` is `{client.command_prefix}{ctx.command.name} {ctx.command.signature}`."
		await ctx.send(embed=embed)
	elif type(exception) is commands.CommandNotFound:
		embed.title = "Invalid command"
		embed.description = f"The command you just tried to use is invalid. Use `{client.command_prefix}help` to see all commands."
		await ctx.send(embed=embed)
	else:
		print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
		traceback.print_exception(type(exception), exception, exception.__traceback__, file=sys.stderr)

class Meta(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self._last_member = None

	@commands.command(brief="show repo")
	async def repo(self, ctx:commands.Context):
		await ctx.send(embed=repomsg)

	@commands.command(brief="give link to support server")
	async def invite(self, ctx:commands.Context):
		await ctx.send("join our support server for support and teasers into new features :)\nhttps://discord.gg/4pUj8vNFXY")

	@commands.command(brief="send bug report to bugs channel in support discord")
	async def bugreport(self, ctx:commands.Context,*report):
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

	@commands.command(brief="send suggestion to feature requests channel in support discord")
	async def suggestion(self, ctx:commands.Context,*report):
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


	@commands.command(brief="show statistics, including usage and amount of servers")
	async def stats(self, ctx:commands.Context):
		with open("analytics.json","r") as analyticsfile: analytics = json.loads(analyticsfile.read())
		embed = discord.Embed(title="Analytics")
		embed.add_field(name="Servers",value=f"{client.user.name} is in {len(client.guilds)} servers.")
		str_usage_stats = ""
		for cmd in analytics:
			str_usage_stats += f"{cmd}: {analytics[cmd]}\n"
		embed.add_field(name="Usage stats",value=str_usage_stats)
		embed.add_field(name="Uptime",value=str(datetime.now() - t0).split(".")[0])
		await ctx.send(embed=embed)

	@commands.command(brief="show latency")
	async def ping(self,ctx:commands.Context):
		await ctx.send(f"Pong! {int(client.latency * 1000)}ms")

client.add_cog(Games(client))
client.add_cog(Fun(client))
client.add_cog(Meta(client))
client.run(token)

# vim: noet ci pi sts=0 sw=4 ts=4: