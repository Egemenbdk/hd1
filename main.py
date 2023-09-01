import discord
from discord import app_commands
from discord.ext import commands
import requests
import random
import time
import asyncio

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)
bot = commands.Bot(command_prefix='!', intents=intents)

inviters = {}
invite_counters = {}

def count_user_warns(user_id):
    return sum(1 for uid, _ in warns_data if uid == user_id)

def save_warns(data):
    with open("warns.txt", "w") as file:
        for user_id, reason in data:
            file.write(f"{user_id} {reason}\n")

def load_warns():
    data = []
    try:
        with open("warns.txt", "r") as file:
            for line in file:
                user_id, reason = line.strip().split(" ", 1)
                data.append((user_id, reason))
    except FileNotFoundError:
        pass
    return data

def load_message_counts():
    message_counts = {}
    try:
        with open('messages.txt', 'r') as file:
            lines = file.readlines()
            for line in lines:
                user_id, count = line.strip().split()
                message_counts[user_id] = int(count)
    except FileNotFoundError:
        pass
    return message_counts

def save_message_counts(message_counts):
    with open('messages.txt', 'w') as file:
        for user_id, count in message_counts.items():
            file.write(f"{user_id} {count}\n")

def is_allowed_role():
    def predicate(ctx):
        allowed_roles = [1145535410064326717, 1143970978305687602, 1143970959125131285]
        return any(role.id in allowed_roles for role in ctx.author.roles)
    return commands.check(predicate)

@client.event
async def on_ready():
    for guild in client.guilds:
        invite_counters[guild.id] = {}
        inviters[guild.id] = {}

@client.event
async def on_member_join(member):
    channel_id = 1136025954926481531
    channel = client.get_channel(channel_id)

    new_invites = await member.guild.invites()

    for new_invite in new_invites:
        if new_invite.uses > invite_counters[member.guild.id].get(new_invite.code, 0):
            inviter = new_invite.inviter
            invite_code = new_invite.code
            invite_counters[member.guild.id][invite_code] = new_invite.uses
            break
    else:
        inviter = None


        welcome_message = (
            f"Welcome to BloxKord 🎉, {member.mention}!\n"
            f"You were invited by {inviter.mention}. Thanks for joining! 😎\n"
        )
    else:
        welcome_message = f"Welcome to BloxKord 🎉, {member.mention}!\nThanks for joining!"

    await channel.send(welcome_message)

@client.event
async def on_member_remove(member):
    guild = member.guild
    if guild.id in inviters:
        for inviter, invites_count in inviters[guild.id].items():
            if inviter.id == member.id:
                inviters[guild.id][inviter] -= 1
                break

@tree.command(name="claim", description="Claim rewards for messages", guild=discord.Object(id=1120175512149565551))
async def claim(interaction):
    message_counts = load_message_counts()
    user_id = str(interaction.user.id)

    if user_id not in message_counts:
        message_counts[user_id] = 0

    if message_counts[user_id] >= 1000:
        reply_embed = discord.Embed(title="Rewards Claimed", description="You have claimed 10000 tokens for 1000 messages. A staff member will contact you shortly.", color=discord.Color.green())
        await interaction.response.send_message(embed=reply_embed)
        
        channel = client.get_channel(1133600770948866098)
        if channel:
            everyone_mention = "||@everyone||"
            await channel.send(everyone_mention)
            
            claim_embed = discord.Embed(description=f"{interaction.user.mention} has claimed 10000 tokens for 1000 messages.", color=discord.Color.blue())
            await channel.send(embed=claim_embed)
        
        message_counts[user_id] -= 1000
        save_message_counts(message_counts)
    else:
        embed = discord.Embed(title="Insufficient Messages", description=f"You only have {message_counts[user_id]} messages. You need 1000.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed)
        save_message_counts(message_counts)

cookies = {
    '.ROBLOSECURITY': '_|WARNING:-DO-NOT-SHARE-THIS.--Sharing-this-will-allow-someone-to-log-in-as-you-and-to-steal-your-ROBUX-and-items.|_EF42C6D4CE39C8B023E7DD69BB210C359376E8CA5563744AEF941E4BB27EE651197D8EB241D14FB374063482E671A01F24E0A1B74DDA74D81FE587B89D17541B397EB1A2CAA6511A04A9700825ACD559F096B2BB2B96DF97AF0DF9B85B027850024AA998CDB393F8AF5250AC1BF813A625E6427862B38C4DCE52594A636BB9742289EC3A06EFF886E5260FF2F7804E982BE726737A4EAC4D1F6CEA40EC5A952A023100C982D4F15A71106111731BBBD71E67C62BF734C83599D0CDC765A2FE320E01913F63F80E9634B9070EC5A40F9097DAA02D6C59B7E1E13BB7EAFDEBA96932936C0A627CB27494140439E45D1703001D60C5D20167094F5C3D217EE73D35AC62E1CC722DD733B3349F55B94B9100DB8412B96D963A7238D5CFDD3DB7E4DFCC45EB157FFDD208C449EF808F7B2A6EBA12D55BFC255C2357A779A9753C8AA0B15F4607D2858FB811D60B1FD1C120A29362FDF9BF8D9AEFF737FB40DAEE04F404836B2759027F6A2502C1E9174C5E56D187E138F8A9155352F3661014CBE3626F3A539B540D1F9ED9405FDF26874587EE8820426D6688D0C5EE70FDF33ADFF564728507C56F41475D8CBBCFEF3E355A922CDED0CE9F0BA874DEC525D492C2B93B8654BA',
}

api_requests_count = 0

def get_user_id(username):
    global api_requests_count
    api_requests_count += 1
    
    search_url = f'https://users.roblox.com/v1/users/search?keyword={username.lower()}&limit=10'
    response = requests.get(search_url).json()

    if 'data' in response and len(response['data']) > 0:
        for user in response['data']:
            if user['name'].lower() == username.lower():
                user_id = user['id']
                return user_id

    return None

def fetch_count(api_url):
    global api_requests_count
    api_requests_count += 1
    
    response = requests.get(api_url, cookies=cookies).json()
    return response.get('count', 0)
    
@tree.command(name="game", description="Game link", guild=discord.Object(id=1120175512149565551))
async def game(interaction):
    await interaction.response.send_message("Game Link: https://www.roblox.com/games/14283172362/Flip-Clicker")
    
@tree.command(name="group", description="Group link", guild=discord.Object(id=1120175512149565551))
async def group(interaction):
    await interaction.response.send_message("Group Link: https://www.roblox.com/groups/32711482/NiteFlex")

@tree.command(name="warn", description="Warn someone", guild=discord.Object(id=1120175512149565551))
async def warn(interaction, member: discord.Member, reason: str):
    allowed_role_ids = [1145535410064326717, 1143970978305687602, 1143971006810173532]
    member_role_ids = [role.id for role in member.roles]

    if any(role_id in allowed_role_ids for role_id in member_role_ids):
        user_id = str(member.id)

        warns_data.append((user_id, reason))
        save_warns(warns_data)

        embed = discord.Embed(title="User Warned", description=f"{member.mention} has been warned. Reason: {reason}")

        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)

@tree.command(name="profile", description="View user's profile", guild=discord.Object(id=1120175512149565551))
async def profile(interaction, user: discord.User):
    user_id = str(user.id)
    user_warns = [(reason, count) for count, (uid, reason) in enumerate(warns_data, start=1) if uid == user_id]

    if not user_warns:
        await interaction.response.send_message(f"{user.mention} has no warnings.")
    else:
        embed = discord.Embed(title=f"{user.name}'s Profile", description=f"Total Warnings: {len(user_warns)}")
        for reason, count in user_warns:
            embed.add_field(name=f"Warning {count}:", value=reason, inline=False)

        await interaction.response.send_message(embed=embed)

@tree.command(name="giveaway", description="Start a giveaway", guild=discord.Object(id=1120175512149565551))
async def start_giveaway(interaction, channel: discord.TextChannel, winners: int, duration: int, *, name: str):
    user = interaction.user
    user_role_ids = [role.id for role in user.roles]

    allowed_role_ids = [1145535410064326717, 1143970978305687602, 1143971006810173532]

    if any(role_id in allowed_role_ids for role_id in user_role_ids):
        start_time_unix = int(time.time())
        end_time_unix = start_time_unix + duration

        end_time_formatted = f"<t:{end_time_unix}:R>"

        embed = discord.Embed(title=f"**{name}**", description=f"**Hosted by:** {user.mention}\n**Winners:** {winners}\n\nReact with 🎉 to participate!\n\nEnds {end_time_formatted}", color=discord.Color.blue())
        message = await channel.send(embed=embed)
        await message.add_reaction("🎉")

        private_reply = "Giveaway started"
        await interaction.response.send_message(private_reply, ephemeral=True)

        participants = {user}

        await asyncio.sleep(duration)
        
        message = await channel.fetch_message(message.id)
        reaction = discord.utils.get(message.reactions, emoji="🎉")

        if reaction and reaction.count > 1:
            async for participant in reaction.users():
                if participant.id != 1145529435416690699:
                    participants.add(participant)
            
            eligible_winners = [participant for participant in participants if participant.id != 1145529435416690699]
            
            if len(eligible_winners) >= winners:
                winners_list = random.sample(eligible_winners, k=winners)
            else:
                winners_list = eligible_winners
            
            winner_mention = " ".join([participant.mention for participant in winners_list])
            winner_message = f"Congratulations {winner_mention}! You've won the {name} giveaway!"
            ended_embed = discord.Embed(title=f"**{name}**", description=f"**Hosted by:** {user.mention}\n**Winners:** {winner_mention}\n\nEnded {end_time_formatted}", color=discord.Color.red())
            await message.edit(embed=ended_embed)
            
            await channel.send(winner_message)
        else:
            ended_embed = discord.Embed(title=f"**{name}**", description=f"**Hosted by:** {user.mention}\n**Winners:** No one\n\nEnded {end_time_formatted}", color=discord.Color.red())
            await message.edit(embed=ended_embed)
            await channel.send(f"Not enough participants to determine a winner for the {name} giveaway. 😔")
    else:
        await interaction.response.send_message("You don't have permission to start a giveaway.", ephemeral=True)

@tree.command(name="info", description="Check user's info", guild=discord.Object(id=1120175512149565551))
async def check_info(interaction, username: str):
    global api_requests_count
    
    user_id = get_user_id(username)

    if user_id:
        followers_url = f'https://friends.roblox.com/v1/users/{user_id}/followers/count'
        followings_url = f'https://friends.roblox.com/v1/users/{user_id}/followings/count'
        friends_url = f'https://friends.roblox.com/v1/users/{user_id}/friends/count'
        user_info_url = f'https://users.roblox.com/v1/users/{user_id}'

        premium_url = f'https://premiumfeatures.roblox.com/v1/users/{user_id}/validate-membership'
        try:
            premium_response = fetch_count(premium_url)
            premium_status = bool(premium_response)
        except:
            premium_status = False

        follower_count = fetch_count(followers_url)
        following_count = fetch_count(followings_url)
        friends_count = fetch_count(friends_url)

        user_info_response = requests.get(user_info_url, cookies=cookies).json()
        bio = user_info_response.get('description', 'No bio available')
        display_name = user_info_response.get('displayName', 'No display name available')

        embed = discord.Embed(title=f"User Info for {username}", color=0x00ff00)
        embed.add_field(name="Premium", value='true' if premium_status else 'false', inline=False)
        embed.add_field(name="Followers", value=follower_count, inline=False)
        embed.add_field(name="Followings", value=following_count, inline=False)
        embed.add_field(name="Friends", value=friends_count, inline=False)
        embed.add_field(name="Bio", value=bio, inline=False)
        embed.add_field(name="Display Name", value=display_name, inline=False)

        avatar_response = requests.get(f'https://www.roblox.com/avatar-thumbnails?params=[{{"userId":{user_id}}}]').json()
        avatar_url = avatar_response[0]['thumbnailUrl']
        embed.set_thumbnail(url=avatar_url)

        await interaction.response.send_message(embed=embed)

    else:
        embed = discord.Embed(title="User Info", color=0xff0000)
        embed.add_field(name="Response", value="Unknown Player", inline=False)
        await interaction.response.send_message(embed=embed)

warns_data = []
warns_data = load_warns()

@bot.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=1120175512149565551))
    print("Bot is ready!")

    await bot.start('also token')

client.run('token')