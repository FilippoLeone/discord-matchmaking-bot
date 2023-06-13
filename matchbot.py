import discord
from discord.ext import commands
from discord.utils import get
import asyncio
import random
import string

intents = discord.Intents.all()  # Create instance of all Intents
bot = commands.Bot(command_prefix='!', intents=intents)  # Define bot and prefix

custom_role_name = 'gamer'  # Define custom role name
sessions = {}  # Sessions dictionary

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.command()
async def create_lobby(ctx, lobby_channel_name: str):
    lobby_channel = get(ctx.guild.voice_channels, name=lobby_channel_name)
    if not lobby_channel:
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(speak=False),
            ctx.guild.me: discord.PermissionOverwrite(read_messages=True)
        }
        await ctx.guild.create_voice_channel(lobby_channel_name, overwrites=overwrites)
        role = get(ctx.guild.roles, name=custom_role_name)
        if not role:
            await ctx.guild.create_role(name=custom_role_name)
    else:
        await ctx.send('Lobby channel already exists.')

@bot.command()
async def create_teams(ctx, lobby_channel_name: str, max_teams: int, team_size: int):
    lobby_channel = get(ctx.guild.voice_channels, name=lobby_channel_name)
    count = len(lobby_channel.members)
    if count < team_size * max_teams:
        await ctx.send("Not enough members in the lobby to create teams.")
        return
    members = lobby_channel.members
    random.shuffle(members)  # Shuffle the members
    # Create a new session
    session_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))
    sessions[session_id] = {}
    for i in range(1, max_teams + 1):
        uid = ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))
        team_category = await ctx.guild.create_category(f'Team {i}-{uid}')
        
        team_members = members[(i-1)*team_size:i*team_size]

        # Store the user context of all members who have joined the team in the session
        sessions[session_id][i] = {member.id: {'member': member, 'team_category': team_category, 'team_text_channel': f'team-{i}-{uid}-text'} for member in team_members}

        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.guild.me: discord.PermissionOverwrite(read_messages=True)
        }
        for member in team_members:
            overwrites[member] = discord.PermissionOverwrite(read_messages=True)
        text_channel = await team_category.create_text_channel(f'team-{i}-{uid}-text', overwrites=overwrites)
        voice_channel = await team_category.create_voice_channel(f'team-{i}-{uid}-voice', overwrites=overwrites)

        for member in team_members:
            await member.move_to(voice_channel)
            participant_role = get(ctx.guild.roles, name=custom_role_name)
            if participant_role:
                await member.add_roles(participant_role)
            else:
                print(f"No role named '{custom_role_name}' exists. Unable to assign role to {member}.")

        print(f'Team {i} created with members: {team_members}.')
        bot.loop.create_task(check_if_empty_and_delete(text_channel, voice_channel, team_category, session_id, i))  # Delete if empty

async def check_if_empty_and_delete(text_channel, voice_channel, category, session_id, team_id):
    """Check if a channel is empty and delete it."""
    while True:
        await asyncio.sleep(10)  # Check every 10 seconds
        if len(voice_channel.members) == 0:  # If the voice channel is empty
            await text_channel.delete()
            await voice_channel.delete()
            if len(category.channels) == 0:  # If there are no more channels in the category
                await category.delete()
                # Remove the team from the session
                sessions[session_id].pop(team_id, None)
                if len(sessions[session_id]) == 0:  # If there are no more teams in the session
                    sessions.pop(session_id, None)  # Delete the session
            break

@bot.command()
async def send_to_teams(ctx, session_number: str, *, message):
    """Command to send a message to a specific session's team text channels."""
    session = sessions.get(session_number)
    if session is None:
        await ctx.send(f'Session {session_number} does not exist.')
        return

    for team_data in session.values():
        for member_id, member_data in team_data.items():
            member = member_data['member']
            channel_name = member_data['team_text_channel']
            channel = discord.utils.get(member_data['team_category'].text_channels, name=channel_name)
            if channel:
                await channel.send(f'{member.mention}: {message}')

    await ctx.send(f'Message broadcasted to all teams in session {session_number}.')


@bot.command()
async def send_to_session(ctx, session_id: str, *, message: str):
    """Command to send a message to all members in a session."""
    session = sessions.get(session_id)
    if session is None:
        await ctx.send(f'Session {session_id} does not exist.')
        return
    for team in session.values():
        for member in team.values():
            await member['member'].send(message)
    await ctx.send(f'Message sent to all members in session {session_id}!')

@bot.command()
async def get_sessions(ctx):
    """Command to get all session ids."""
    if not sessions:
        await ctx.send("No active sessions.")
    else:
        await ctx.send("Active session IDs: " + ", ".join(sessions.keys()))

bot.run('your-token')
