# Discord Matchmaking Bot

This bot is a tool for automatically organizing and managing game sessions on a Discord server. The bot will create voice and text channels for teams, move members to their respective team channels, and manage session communication.

## Getting Started

1. Clone this repository.
2. Install the discord.py library (version 1.7 or later) by running the following command: `pip install discord.py`.
3. Create a Discord bot and copy its token. For more information, refer to [Discord's documentation](https://discord.com/developers/docs/intro).
4. Replace `token` at the bottom of the code with your bot's token.

## Usage

Once the bot is running on your server, you can use the following commands:

1. `!create_lobby [lobby_channel_name]`: Creates a lobby voice channel where members can join to be included in the matchmaking.

2. `!create_teams [lobby_channel_name] [max_teams] [team_size]`: Creates a specified number of teams from the members present in the lobby. Each team will have its own text and voice channel.

3. `!send_to_teams [session_id] [message]`: Sends a message to the text channel of each team in a specific session.

4. `!send_to_session [session_id] [message]`: Sends a private message to all members in a specific session.

5. `!get_sessions`: Lists all active session IDs.

6. `!schedule_autostart [lobby_channel_name] [min_max_teams] [min_max_team_size] [time_to_wait] [teams_channel_message] [private_individual_message] [keep_autostart]`: Schedules automatic team creation when a minimum number of players is reached in the lobby.

7. `!stop_autostart [lobby_channel_name]`: Stops the scheduled autostart for a specific lobby.

8. `!stop_all_autostarts`: Stops all scheduled autostarts.

9. `!help`: List all commands.

10. `!help [command_name]`: Gives you specific information about the command. 

## Example Usage

`!schedule_autostart queue-channel 3/5 2/3 5 custom-lobby-password-here "Good luck in your custom game!"`

## Permissions

The bot requires the following permissions:

### Bot Role Permissions:

- Read Messages
- Send Messages
- Manage Channels
- Move Members
- Read Message History
- Connect
- Speak

Make sure to grant the bot role these permissions in the server where you want to use the bot.

## Technical Details

### Intents

The bot uses Discord's Intent feature to receive certain gateway events. This bot uses all Intents to ensure it receives all necessary events.

### Sessions

The bot uses a dictionary to keep track of all sessions. Each session has a unique ID and contains a dictionary for each team. The team dictionary maps each member's ID to a context object, which contains the member and their team's category.

### Channel Cleanup

The bot periodically checks if a team's voice channel is empty. If it is, it deletes the team's text and voice channels and the team's category if there are no more channels in it. If there are no more teams in a session, it deletes the session.

## Note

This bot does not manage game servers or integrate with any specific game. It is purely for managing teams and sessions within Discord. Any integration with a game server or API would need to be added separately.
