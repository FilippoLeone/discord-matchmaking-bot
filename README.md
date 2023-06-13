# Discord Matchmaking Bot

The Discord Matchmaking Bot is designed to facilitate the organization and management of gaming sessions on Discord servers. It provides a streamlined way to create, organize, and manage game sessions by creating separate voice and text channels for teams, shifting members to their respective team channels, and handling session-wide communication.

## Setting Up the Bot

1. Clone this repository to your local machine.
2. Install the discord.py library, preferably version 1.7 or newer. You can use the pip package manager: `pip install discord.py`.
3. Register and set up a Discord bot, then retrieve its token. More information can be found in the [Discord Developer Documentation](https://discord.com/developers/docs/intro).
4. Replace `token` at the end of the code with your bot's token.

## Bot Command Usage

When the bot is live on your server, it recognizes the following commands:

1. `!create_lobby [lobby_channel_name]`: This command creates a voice channel named 'lobby', where members can join for matchmaking. It also creates a 'gamer' role.

2. `!create_teams [lobby_channel_name] [max_teams] [team_size]`: From the members in the lobby, this command creates a given number of teams. Each team gets a dedicated voice and text channel.

3. `!send_to_teams [session_id] [message]`: Sends a provided message to the text channels of all teams in a specified session.

4. `!send_to_session [session_id] [message]`: Sends a private message to all participants in a particular session.

5. `!schedule_autostart [lobby_channel_name] [min_max_teams] [min_max_team_size] [time_to_wait] [keep_autostart]`: Schedules an autostart that creates teams as soon as the minimum number of players join the lobby, waits for a specified period and then starts the game. The 'keep_autostart' flag can be set to True to have the autostart run continuously.

6. `!stop_autostart [lobby_channel_name]`: Stops the scheduled autostart for a particular lobby.

7. `!stop_all_autostarts`: Stops all scheduled autostarts on the server.

8. `!get_sessions`: Displays a list of all active session IDs.

## Technical Specifications

### Discord Intents

The bot uses Discord's Intent feature to receive specific gateway events. All Intents are enabled for this bot to ensure it receives every necessary event.

### Roles and Permissions

The bot creates a 'gamer' role for users who join the lobby. When channels are created, permissions are set so that only users with the 'gamer' role can view the channel.

### Sessions Management

Sessions are tracked using a dictionary, where each session has a unique ID. The dictionary for each session contains a mapping for each team, linking each member's ID to a context object which includes the member and their team's category.

### Channel Cleanup Mechanism

The bot periodically verifies if a team's voice channel is vacant. If it is, the bot removes the team's text and voice channels, and if there are no remaining channels in the category, the category itself is deleted. If there are no more teams left in a session, the session is also deleted.

## Limitations

While this bot excels at managing teams and sessions within Discord, it does not handle game servers or integrates with any particular game. Any necessary integration with a game server or API will have to be separately added to the bot's functionalities.
