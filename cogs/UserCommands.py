import logging
from datetime import datetime

import discord
from classes.Embeds import ProfileEmbed
from discord.ext import commands
from discord.ext.commands.core import guild_only
from models.UserRepository import UserRepository
from utils.const import PROFILE_LIST_FIELDS, PROFILE_STRING_FIELDS

logger = logging.getLogger('botlogs')


class UserCommands(commands.Cog, name="Users"):
    def __init__(self, bot):
        self.bot = bot
        self.user_repo = UserRepository()

    @commands.command(
        description="Registers/updates a user's info with the bot",
        usage="register [@user]", aliases=['update', 'reg'])
    @guild_only()
    async def register(self, ctx, user: discord.Member = None):
        if user is None:
            user = ctx.author
        async with ctx.typing():
            if self.user_repo.read({"id": user.id}) is None:
                self.user_repo.insert({
                    "id": user.id,
                    "name": user.name,
                    "discriminator": user.discriminator,
                    "display_name": user.display_name,
                    "joined_at": datetime.now().timestamp()
                })
            else:
                self.user_repo.update({"id": user.id}, {"$set": {
                    "name": user.name,
                    "discriminator": user.discriminator,
                    "display_name": user.display_name,
                }})
        return await ctx.message.add_reaction("✅")

    # @commands.command(name="mu",
    #                   description="Adds all the members of the server in the db",
    #                   usage="mu",
    #                   aliases=["massupdate"])
    # @commands.cooldown(rate=1, per=1.5, type=commands.BucketType.user)
    # @commands.has_role("Admin")
    # @guild_only()
    # async def mass_update(self, ctx):
    #     for i, user in enumerate(self.bot.guilds[0].members):
    #         if self.user_repo.read({"id": user.id}) is None:
    #             self.user_repo.insert({
    #                 "id": user.id,
    #                 "name": user.name,
    #                 "discriminator": user.discriminator,
    #                 "display_name": user.display_name,
    #                 "joined_at": datetime.now().timestamp()
    #             })
    #         print(i)
    #     return await ctx.send("Users db updated")

    @commands.group(
        description="Shows a user's server profile",
        usage="profile <@user>", aliases=["pr"], case_insensitive=True)
    async def profile(self, ctx, user: discord.Member):
        if ctx.invoked_subcommand is None:
            async with ctx.typing():
                user_doc = self.user_repo.read({"id": user.id})
                try:
                    thumbnail = user.avatar.url
                except Exception:
                    thumbnail = None
                embed = ProfileEmbed(bot=self.bot, thumbnail=thumbnail)
                embed.create(user_doc)
            return await ctx.send(embed=embed)
        return

    @profile.command(
        name="setup", description="Starts process for server profile setup",
        usage="profile <@user> setup")
    async def setup(self, ctx):
        await ctx.send("Hello! You're about to set your server profile!"
                       " You can cancel at any time by typing `cancel`")

        def check(m):
            return m.channel == ctx.channel and m.author == ctx.author
        timeout_dur = 360.0
        field = "about"
        field_prompt = ("First, enter some general information yourself."
                        " For example - Hey, I'm <name> and I'm a <age> year old guy/girl who"
                        " likes to read and <stuff>")
        if not await self.wait_for_input(ctx, check, field_prompt, field, timeout_dur):
            return await ctx.send("Cancelling ...")

        field = "reading"
        field_prompt = (
            "Now, Enter a list of books you're reading, separated by a '|'."
            " You may mention the author too."
            " For example - Pride & Prejudice(Jane Austen)|Crime & Punishment")
        if not await self.wait_for_input(ctx, check, field_prompt, field, timeout_dur):
            return await ctx.send("Cancelling ...")

        field = "authors"
        field_prompt = (
            "Now, Enter a list of your top authors, separated by '|'. "
            "For example - Jane Austen|Sarah J. Maas")
        if not await self.wait_for_input(ctx, check, field_prompt, field, timeout_dur):
            return await ctx.send("Cancelling ...")

        field = "genres"
        field_prompt = (
            "Now, Enter a list of your top genres, separated by '|'. "
            "For example - Fiction|Fantasy|Science Fiction")
        if not await self.wait_for_input(ctx, check, field_prompt, field, timeout_dur):
            return await ctx.send("Cancelling ...")

        field = "goodreads"
        field_prompt = (
            "Now, If you have a Goodreads or a Storygraph account, "
            "enter the link to your profile.")
        if not await self.wait_for_input(ctx, check, field_prompt, field, timeout_dur):
            return await ctx.send("Cancelling ...")
        return await ctx.send("Profile setup is complete!")

    @profile.command(
        name="set", description="Set a field for your profile",
        usage="profile @user set <field> <value>", aliases=["edit"])
    async def set_field(self, ctx, field, *, value: str):
        if field.lower() in PROFILE_STRING_FIELDS:
            update = {PROFILE_STRING_FIELDS[field.lower()]: value}
        elif field.lower() in PROFILE_LIST_FIELDS:
            list_delimiter = "|"
            new_vals = [val.strip() for val in value.split(list_delimiter)]

            update = {PROFILE_LIST_FIELDS[field.lower()]: new_vals}
        else:
            return await ctx.reply("Invalid field. Cancelling...")
        async with ctx.typing():
            self.user_repo.update({"id": ctx.author.id}, {"$set": update})
        return await self.profile(ctx, ctx.author)

    @profile.command(
        name="unset", description="Unsets a field for your profile",
        usage="profile @user unset <field>")
    async def unset_field(self, ctx, field):
        if field.lower() in PROFILE_STRING_FIELDS:
            update = {PROFILE_STRING_FIELDS[field.lower()]: ""}
        elif field.lower() in PROFILE_LIST_FIELDS:
            update = {PROFILE_LIST_FIELDS[field.lower()]: []}
        else:
            return await ctx.reply("Invalid field. Cancelling...")
        async with ctx.typing():
            self.user_repo.update({"id": ctx.author.id}, {"$unset": update})
        return await self.profile(ctx, ctx.author)

    @profile.command(
        name="add", description="Adds a value to a list field for your profile",
        usage="profile @user add <field> <value>", aliases=["push"])
    async def add_values_to_field(self, ctx, field, *, value: str):
        if field.lower() in PROFILE_LIST_FIELDS:
            async with ctx.typing():
                list_delimiter = "|"
                new_vals = [val.strip() for val in value.split(list_delimiter)]
                update = {PROFILE_LIST_FIELDS[field.lower()]: {
                    "$each": new_vals}}
                self.user_repo.update({"id": ctx.author.id}, {"$push": update})
        else:
            return await ctx.reply("Invalid field. Cancelling...")
        return await self.profile(ctx, ctx.author)

    @profile.command(
        name="remove",
        description="Removes a value (by index) from a list field for your server profile",
        usage="profile @user remove <field> <index>", aliases=["pop"])
    async def remove_values_from_field(self, ctx, field, *, value: int):
        if field.lower() in PROFILE_LIST_FIELDS:
            async with ctx.typing():
                old_user = self.user_repo.read({"id": ctx.author.id})
                old_list = old_user[PROFILE_LIST_FIELDS[field.lower()]]
                value = value - 1
                if value < 0 or value >= len(old_list):
                    return await ctx.reply("Invalid index. Cancelling...")
                del old_list[value]
                update = {PROFILE_LIST_FIELDS[field.lower()]: old_list}
                self.user_repo.update({"id": ctx.author.id}, {"$set": update})
        else:
            return await ctx.reply("Invalid field. Cancelling...")
        return await self.profile(ctx, ctx.author)

    @profile.command(
        name="clear", description="Resets your server profile",
        usage="profile @user clear", aliases=['reset'])
    async def clear(self, ctx):
        async with ctx.typing():
            self.user_repo.update({"id": ctx.author.id}, {"$unset": {
                                  "description": "",
                                  "profile_link": "",
                                  "curr_reading": "",
                                  "top_genres": "",
                                  "top_authors": ""}})
        return await ctx.reply("Profile cleared")

    @profile.command(
        name="reading", description="Shows just the reading section of your profile",
        usage="profile @user reading", aliases=['CR', 'r'])
    async def reading(self, ctx):
        async with ctx.typing():
            user_doc = self.user_repo.read({"id": ctx.author.id})
            user_read_doc = {}
            user_read_doc['curr_reading'] = user_doc['curr_reading']
            user_read_doc['display_name'] = user_doc['display_name']
            try:
                thumbnail = ctx.author.avatar.url
            except Exception:
                thumbnail = None
            embed = ProfileEmbed(bot=self.bot, thumbnail=thumbnail)
            embed.create(user_read_doc)
        try:
            await ctx.message.delete()
        except Exception:
            pass
        return await ctx.send(embed=embed)

    async def wait_for_input(self, ctx, check, prompt, field, timeout_dur):
        await ctx.send(prompt)
        await ctx.send("Type `skip` to skip this section")
        try:
            desc = await self.bot.wait_for("message", timeout=timeout_dur, check=check)
        except Exception:
            return False
        if str(desc.content).lower() == "cancel":
            return False
        elif str(desc.content).lower() == "skip":
            await ctx.send("Skipping ...")
        else:
            await self.set_field(ctx, field=field, value=str(desc.content))
        return True


def setup(bot):
    bot.add_cog(UserCommands(bot))
