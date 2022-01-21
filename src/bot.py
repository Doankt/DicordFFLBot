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
import firebasetools
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
@bot.command(aliases=['r'], description="Get the rankings of a player")
async def rankings(ctx, log_link):
    # Parse the log link
    parsed_url = urlparse(log_link)
    parse_path = parsed_url.path.split('/')
    
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

    # Build time dict (id:killtime)
    time_dict = {f['id'] : f['endTime'] - f['startTime'] for f in res['data']['reportData']['report']['fights']}
    # Build rankings dict (id:json)
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
            tbl = tabulate(tfight, headers=['Name', 'Job', 'Rank', '%'], tablefmt='github'),
            fight_time = ms_to_mmssms(time_dict[i])
        )
    )

@bot.group(desctiption= "Gets info about yourself", pass_context=True)
async def me(ctx):
    if ctx.invoked_subcommand is None:
        # If no args, get the user's fflogs id
        fflogs_id = firebasetools.get_fflogs_id(ctx.author.id)
        if fflogs_id is None:
            await ctx.send("`You don't have a fflogs id set`")
            return

        # Do things here
        q = '''
        {
            characterData{
                character(id: %s){
                    name,
                    server{
                        name,
                        subregion{
                            name
                        }
                    },
                    zoneRankings
                }
            }
        }
        ''' % fflogs_id

        res = ff_client.query(q)
        character = res['data']['characterData']['character']

        # Build table
        tbl = []
        for fight in character['zoneRankings']['rankings']:
            tbl.append([
                fight['encounter']['name'],
                "{0:.1f}".format(fight['rankPercent']) if fight['rankPercent'] is not None else "-",
                definitions.CLASS_ACRO_MAP[fight['spec']] if fight['spec'] is not None else "-",
                fight['totalKills'],
                ms_to_mmssms(fight['fastestKill']) if fight['fastestKill'] != 0 else "-",
                fight['allStars']['rank'] if fight['allStars'] is not None else "-",
            ])
        
        await ctx.send(
            "`" +
            tabulate(tbl, headers=['Encounter', '%', 'Job', 'Kills', 'Fastest Kill', 'Rank'], tablefmt='github')
            + "`"
        )

@me.command(invoke_without_command=True, aliases=["set"])
async def set_user(ctx, fflogs_url):
    # Parse the log link
    parsed_url = urlparse(fflogs_url)
    parse_path = parsed_url.path.split('/')
    # Assert the first path segment is "character"
    if parse_path[1] != 'character' or parse_path[2] != 'id':
        await ctx.send('`Invalid link / Not a character link`')
        return
    # Get the last location of the path
    fflogs_id = parse_path[3]
    firebasetools.update_user(ctx.author.id, fflogs_id)
    await ctx.send("`User set to %s`" % fflogs_id)

@me.command(invoke_without_command=True, aliases=["remove"])
async def remove_user(ctx):
    ret = firebasetools.remove_user(ctx.author.id)
    if ret:
        await ctx.send("`FFLogs ID removed`")
    else:
        await ctx.send("`No FFLogs ID to remove`")


bot.run(os.environ.get("discord_token"))