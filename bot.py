# Discord imports
# import discord
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
from timetools import ms_to_mmssms
import definitions

# Other imports
import asyncio

# Define Client and Bot
bot = commands.Bot(command_prefix='?')
ff_client = FFLogsOAuth(os.getenv("client_id"), os.getenv("client_secret"))

# Ready Message
@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

# Rankings Command
@bot.command(aliases=['r'])
async def rankings(ctx, log_link):
    # Parse the log link
    parsed_url = urlparse(log_link)
    parse_path = parsed_url.path.split('/')
    
    print(parse_path)
    print(parse_path[2])
    
    # Assert the first path segment is "reports"
    if parse_path[1] != 'reports':
        await ctx.send('Invalid log link / Not a report link')
        return

    # Get the last location of the path
    report_id = parse_path[2]
    
    # Query
    q = '''
    {
        reportData{
            report(code: "%s"){
                fights{
                    id,
                    startTime,
                    endTime
                },
                rankings
            }
        }
    }
    ''' % report_id

    res = ff_client.query(q)

    # if 'errors' in res: 

    # Build time dict
    time_dict = {f['id'] : f['endTime'] - f['startTime'] for f in res['data']['reportData']['report']['fights']}
    # Build rankings dict
    rankings_dict = {f['fightID'] : f for f in res['data']['reportData']['report']['rankings']['data']}

    # Check < 1 clears
    clear_count = len(res['data']['reportData']['report']['rankings']['data'])
    if clear_count == 0:
        await ctx.send('`No rankings found`')
        return
    elif clear_count == 1:
        fight = list(rankings_dict.values())[0]
        i = fight['fightID']
    else:
        # Prompt user to select a fight
        tmp_table = []
        for fight in res['data']['reportData']['report']['rankings']['data']:
            tmp_table.append([fight['fightID'], fight['encounter']['name'], ms_to_mmssms(time_dict[fight['fightID']])])
        
        pmt_msg = await ctx.send("`Enter the fight number you want to see rankings for\n"
            + tabulate(tmp_table, headers=['Num', 'Fight', 'Time'], tablefmt='github')
            + "`"
        )

        # Validate user input
        def response_check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel

        try:
            msg = await bot.wait_for('message', check=response_check, timeout=30.0)
            i = int(msg.content)
            
            # Select the fight
            fight = rankings_dict[i]
        except (IndexError, KeyError):
            await ctx.send("`Invalid fight number`")
            await msg.delete()
            return
        except asyncio.TimeoutError:
            await ctx.send('`Request timed out`')
            return
        except ValueError:
            await ctx.send('`Invalid input`')
            await msg.delete()
            return
        finally:
            await pmt_msg.delete()
        await msg.delete()
    
    
    # Format and send
    tfight = []
    for role in fight['roles'].values():
        for player in role['characters']:
            if 'server' not in player:    continue
            
            player_para = [
                player['name'],
                definitions.CLASS_ACRO_MAP[player['class']],
                player['rank'],
                player['rankPercent']
            ]
            tfight.append(player_para)
    
    await ctx.send(
        "`{encounter_name} - {fight_time}\n{tbl}`\n".format(
            encounter_name = fight['encounter']['name'],
            tbl = tabulate(tfight, headers=['Name', 'Role', 'Rank', '%'], tablefmt='github'),
            fight_time = ms_to_mmssms(time_dict[i])
        )
    )

bot.run(os.environ.get("discord_token"))