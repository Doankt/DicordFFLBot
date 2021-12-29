# Discord imports
import discord
import discord.ext.commands as commands

# .env imports
import os
from dotenv import load_dotenv
load_dotenv(".env")

# Formatting imports
from urllib.parse import urlparse
from tabulate import tabulate

# User imports
from fflogsoauth import FFLogsOAuth

# Define Client and Bot
bot = commands.Bot(command_prefix='!')
ff_client = FFLogsOAuth(os.getenv("client_id"), os.getenv("client_secret"))

# Ready Message
@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

# Rankings Command
@bot.command()
async def rankings(ctx, log_link):
    # Parse the log link
    parsed_url = urlparse(log_link)

    # Assert the first path segment is "reports"
    if parsed_url.path.split('/')[1] != 'reports':
        await ctx.send('Invalid log link / Not a report link')
        return

    # Get the last location of the path
    report_id = parsed_url.path.split('/')[-1]

    # Query
    q = '''
    {
        reportData{
            report(code: "%s"){
                rankings
            }
        }
    }
    ''' % report_id

    res = ff_client.query(q)
    
    # Format and send
    for fight in res['data']['reportData']['report']['rankings']['data']:
        if not fight['kill']: continue
        tfight = []

        for role in fight['roles'].values():
            for player in role['characters']:
                if 'server' not in player:    continue
                
                player_para = [
                    player['name'],
                    player['rank'],
                    player['rankPercent']
                ]
                tfight.append(player_para)
        
        await ctx.send(
            "`{encounter_name}\n{tbl}`\n".format(
                encounter_name = fight['encounter']['name'],
                tbl = tabulate(tfight, headers=['Name', 'Rank', 'Rank %'], tablefmt='github')
            )
        )

bot.run(os.environ.get("discord_token"))