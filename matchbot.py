import discord
from discord.ext import commands
from discord.utils import get
import asyncio
import random
import string
import trueskill

intents = discord.Intents.all()  # Create instance of all Intents
bot = commands.Bot(command_prefix='!', intents=intents)  # Define bot and prefix

sessions = {}  # Sessions dictionary

@bot.event
async def on_ready():
    print(f'Bot is now active as: {bot.user}')

@bot.command()
@commands.has_permissions(administrator=True)
async def create_lobby(ctx, lobby_channel_name: str):
    lobby_channel = get(ctx.guild.voice_channels, name=lobby_channel_name)
    if not lobby_channel:
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(speak=False),
            ctx.guild.me: discord.PermissionOverwrite(read_messages=True)
        }
        await ctx.guild.create_voice_channel(lobby_channel_name, overwrites=overwrites)
    else:
        await ctx.send('Lobby channel already exists.')

@bot.command()
@commands.has_permissions(administrator=True)
async def create_teams(ctx, lobby_channel_name: str, max_teams: int, team_size: int):
    lobby_channel = get(ctx.guild.voice_channels, name=lobby_channel_name)
    count = len(lobby_channel.members)
    if count < team_size * max_teams:
        await ctx.send("Not enough members in the lobby to create teams.")
        return
    members = lobby_channel.members
    random.shuffle(members)  # Shuffle the members

    session_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))  # Create a new session id
    sessions[session_id] = {}

    for i in range(1, max_teams + 1):
        uid = ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))
        team_category = await ctx.guild.create_category(f'Team {i}-{uid}')
        
        team_members = members[(i-1)*team_size:i*team_size]

        # Store the user context of all members who have joined the team in the session
        sessions[session_id][i] = {member.id: {'member': member, 'team_category': team_category, 'team_text_channel': f'team-{i}-{uid}-text'} for member in team_members}

        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False, connect=False),
            ctx.guild.me: discord.PermissionOverwrite(read_messages=True, connect=True)
        }

        for member in team_members:
            overwrites[member] = discord.PermissionOverwrite(read_messages=True, connect=True, speak=True)

        text_channel = await team_category.create_text_channel(f'team-{i}-{uid}-text', overwrites=overwrites)
        voice_channel = await team_category.create_voice_channel(f'team-{i}-{uid}-voice', overwrites=overwrites)

        for member in team_members:
            await member.move_to(voice_channel)

        print(f'Team {i} created with members: {team_members}.')
        bot.loop.create_task(check_if_empty_and_delete(text_channel, voice_channel, team_category, session_id, i))  # Delete if empty
    return f"{session_id}"

async def check_if_empty_and_delete(text_channel, voice_channel, category, session_id, team_id):
    """Check if a channel is empty and delete it."""
    while True:
        await asyncio.sleep(30)  # Check every 10 seconds
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
@commands.has_permissions(administrator=True)
async def send_to_teams(ctx, session: str, message: str):
    """Command to send a message to a specific session's team text channels."""
    session = sessions.get(session)
    if session is None:
        await ctx.send(f'Session {session} does not exist.')
        return

    for team_data in session.values():
        for member_id, member_data in team_data.items():
            member = member_data['member']
            channel_name = member_data['team_text_channel']
            channel = discord.utils.get(member_data['team_category'].text_channels, name=channel_name)
            if channel:
                await channel.send(f'{member.mention}: {message}')

    await ctx.send(f'Message broadcasted to all teams in session.')


@bot.command()
@commands.has_permissions(administrator=True)
async def send_to_session(ctx, session: str, message: str):
    """Command to send a message to all members in a session."""
    session = sessions.get(session)
    if session is None:
        await ctx.send(f'Session {session} does not exist.')
        return
    for team in session.values():
        for member in team.values():
            await member['member'].send(message)
    await ctx.send(f'Message sent to all members in session!')

autostart_tasks = {}  # A dictionary to store autostart tasks

@bot.command()
@commands.has_permissions(administrator=True)
async def schedule_autostart(ctx, lobby_channel_name: str, min_max_teams: str, min_max_team_size: str, time_to_wait: int, start_message: str, private_message: str, keep_autostart: bool = False):
    min_teams, max_teams = map(int, min_max_teams.split("/"))
    min_team_size, max_team_size = map(int, min_max_team_size.split("/"))
    
    # Check if the lobby channel exists or create it if it doesn't
    lobby_channel = get(ctx.guild.voice_channels, name=lobby_channel_name)
    if not lobby_channel:
        await ctx.invoke(bot.get_command('create_lobby'), lobby_channel_name=lobby_channel_name)
        lobby_channel = get(ctx.guild.voice_channels, name=lobby_channel_name)

    await ctx.send(f'Scheduled autostart activated for {lobby_channel_name}.')

    # Schedule the autostart
    autostart_task = bot.loop.create_task(run_autostart(ctx, lobby_channel, min_teams, max_teams, min_team_size, max_team_size, time_to_wait, start_message, private_message, keep_autostart))

    # Store the task in the dictionary using the lobby channel name as the key
    autostart_tasks[lobby_channel_name] = autostart_task

async def run_autostart(ctx, lobby_channel, min_teams, max_teams, min_team_size, max_team_size, time_to_wait, start_message, private_message, keep_autostart):
    game_in_progress = False
    while True:  # keep running until keep_autostart is set to False
        await asyncio.sleep(1)  # Check every second
        if len(lobby_channel.members) >= min_team_size * min_teams and not game_in_progress:
            # If maximum number of players reached, start the game immediately
            if len(lobby_channel.members) >= max_team_size * max_teams:
                print(f'Maximum player count reached in {lobby_channel.name}. Starting the game...')
                await ctx.send(f'Maximum player count reached. Starting the game...')
                create_teams_command = bot.get_command('create_teams')
                session_id = await create_teams_command.callback(ctx, lobby_channel_name=lobby_channel.name, max_teams=max_teams, team_size=max_team_size)
                if session_id:  # Check that session_id is not None
                    await asyncio.sleep(10)
                    await ctx.send(f'Sending messages to session_id {session_id}.')
                    await ctx.invoke(bot.get_command('send_to_teams'), session_id, start_message)  # Send the start message
                    await ctx.invoke(bot.get_command('send_to_session'), session_id, private_message)  # Send the start message
                game_in_progress = True
            else:
                print(f'Minimum player count reached in {lobby_channel.name}. Waiting for {time_to_wait} minute(s)...')
                await ctx.send(f'Minimum player count reached. Waiting for {time_to_wait} minute(s)...')
                await asyncio.sleep(time_to_wait * 60)  # wait for specified minutes after reaching minimum players
                print(f'Timeout reached in {lobby_channel.name}. Starting the game...')
                await ctx.send(f'Starting the game...')
                create_teams_command = bot.get_command('create_teams')
                session_id = await create_teams_command.callback(ctx, lobby_channel_name=lobby_channel.name, max_teams=max_teams, team_size=max_team_size)
                if session_id:  # Check that session_id is not None
                    await asyncio.sleep(10)
                    await ctx.send(f'Sending messages to session_id {session_id}.')
                    await ctx.invoke(bot.get_command('send_to_teams'), session_id, start_message)  # Send the start message
                    await ctx.invoke(bot.get_command('send_to_session'), session_id, private_message)  # Send the start message
                game_in_progress = True

        elif game_in_progress:
            if not keep_autostart:
                break  # break the outer loop if keep_autostart is False

            # Clear lobby and start again
            lobby_channel = get(ctx.guild.voice_channels, name=lobby_channel.name)
            game_in_progress = False



@bot.command()
@commands.has_permissions(administrator=True)
async def stop_autostart(ctx, lobby_channel_name: str):
    # Cancel the task for the given lobby
    if lobby_channel_name in autostart_tasks:
        autostart_tasks[lobby_channel_name].cancel()
        del autostart_tasks[lobby_channel_name]  # Remove the task from the dictionary
        await ctx.send(f'Scheduled autostart stopped for {lobby_channel_name}.')
    else:
        await ctx.send(f'No scheduled autostart found for {lobby_channel_name}.')

@bot.command()
@commands.has_permissions(administrator=True)
async def stop_all_autostarts(ctx):
    # Cancel all autostart tasks
    for task in autostart_tasks.values():
        task.cancel()
    autostart_tasks.clear()  # Clear the dictionary
    await ctx.send('All scheduled autostarts have been stopped.')

@bot.command()
@commands.has_permissions(administrator=True)
async def get_sessions(ctx):
    """Command to get all session ids."""
    if not sessions:
        await ctx.send("No active sessions.")
    else:
        await ctx.send("Active session IDs: " + ", ".join(sessions.keys()))

bot.run('your-token')
