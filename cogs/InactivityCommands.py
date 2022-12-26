from utils.views import Paginator
from classes.Embeds import InactiveUsersEmbed
from datetime import datetime

import discord
from discord.ext import commands
from discord.ext.commands.core import guild_only
from models.UserRepository import UserRepository


class InactivityCommands(commands.Cog, name="Inactivity"):

    def __init__(self, bot):
        self.bot = bot
        self.user_repo = UserRepository()

    @commands.Cog.listener("on_message")
    async def update_last_message_timestamp(self, message):
        if message.author.bot or len(message.content) < 5:
            return
        timestamp = datetime.now().timestamp()
        if self.user_repo.read({"id": message.author.id}) is None:
            self.user_repo.insert({
                "id": message.author.id,
                "name": message.author.name,
                "discriminator": message.author.discriminator,
                "display_name": message.author.display_name,
                "joined_at": timestamp})
        return self.user_repo.update(
            {"id": message.author.id}, {"$set": {"last_message_at": timestamp}})

    @commands.command(
        name="timelookup",
        description="Gets the time of last sent message from a user",
        usage="timeLookup <user>",
        aliases=["tl"])
    @commands.cooldown(rate=1, per=1.5, type=commands.BucketType.user)
    @commands.has_role("Staff")
    @guild_only()
    async def time_lookup(self, ctx, user: discord.Member):
        async with ctx.typing():
            dbuser = self.user_repo.read({"id": user.id})
            timestamp = dbuser["last_message_at"]
            author = ctx.message.author
            e = discord.Embed(title=f"User Lookup for {user.display_name}",
                              description=f"{user.display_name} last sent a message at <t:{int(timestamp)}>, \
                                            which was <t:{int(timestamp)}:R>",
                              color=discord.Color.green())
            e.set_author(name=author.nick,
                         url=author.avatar.url)
            e.set_thumbnail(url=user.avatar.url)
            e.set_footer(text="Fetched from MongoDB storage by {}".format(
                self.bot.user.name))
        await ctx.send(embed=e)

    @commands.command(name="timelist",
                      description=("Gets the list of users "
                                   "whose last message is older than the given date"),
                      usage="ut <date (in YYYY-MM-DD format)>",
                      aliases=["lt", "tu"])
    @commands.cooldown(rate=1, per=1.5, type=commands.BucketType.user)
    @commands.has_role("Staff")
    @guild_only()
    async def time_list(self, ctx, date):
        timestamp = datetime.strptime(date, "%Y-%m-%d").timestamp()
        async with ctx.typing():
            inactive_users = list(self.user_repo.read_many(
                {"$or": [{"last_message_at": {"$lt": int(timestamp)}},
                         {"last_message_at": None},
                         {"last_message_at": {"$exists": False}}]}))
            temp_users = []
            all_pages = []
            for i, user in enumerate(inactive_users):
                temp_users.append(user)
                if i != 0 and i % 20 == 0:
                    embed = InactiveUsersEmbed()
                    embed.create(temp_users)
                    temp_users = []
                    all_pages.append(embed)
            if len(temp_users) != 0:
                embed = InactiveUsersEmbed()
                embed.create(temp_users)
                all_pages.append(embed)
        for i, page in enumerate(all_pages):
            page.set_footer(
                text=f"Use buttons to flip pages. (Page {i + 1}/{len(all_pages)})")
        view = Paginator(all_pages)
        if len(all_pages) == 0:
            return await ctx.send("No users found for given date")
        return await ctx.send(embed=all_pages[0], view=view)


def setup(bot):
    bot.add_cog(InactivityCommands(bot))
