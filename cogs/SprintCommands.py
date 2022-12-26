import asyncio
import logging

import discord
from discord.ext import commands
from discord.ext.commands.core import guild_only
from models.Sprint import Sprint
from models.SprintRepository import SprintRepository
from utils.const import PREFIX, YOU_ARE_A_DUMBASS_GIF
from utils.views import Confirm

logger = logging.getLogger('botlogs')


class SprintCommands(commands.Cog, name="Sprints"):
    def __init__(self, bot):
        self.bot = bot
        self.timeout_duration = 60
        self.sprints = {}
        self.end_wait_min = 2

    @commands.Cog.listener()
    async def on_sprint_finish(self, sprint_id):
        if sprint_id not in self.sprints:
            logger.error("A deleted/cancelled sprint has finished :O")
        curr_sprint = self.sprints[sprint_id]
        mentions = self.get_participant_mentions(curr_sprint)
        channel = self.bot.get_channel(sprint_id)
        curr_sprint.end_counts = {}
        await channel.send(
            f"{mentions}\n"
            f"📚📚📚 **SPRINT ENDED** 📚📚📚")
        await channel.send(
            f"Please send your updated page/word count by using"
            f" `{PREFIX}sprint count <num>` within {self.end_wait_min} minutes\n")
        await asyncio.sleep(self.end_wait_min * 60)
        if sprint_id in self.sprints:
            await self.display_sprint_stats(sprint_id)
            sprint_repo = SprintRepository()
            sprint_repo.save(curr_sprint)
            del self.sprints[sprint_id]
        return

    @commands.guild_only()
    @commands.group(
        name="sprint", description="Shows the status of the current ongoing sprint",
        usage="sprint", aliases=["sp"], case_insensitive=True)
    @guild_only()
    async def sprint(self, ctx):
        if ctx.invoked_subcommand is None:
            if not await self.is_sprint_ongoing(ctx.channel.id):
                return await ctx.reply("There are no scheduled/ongoing sprints in this channel.")
            curr_sprint = self.sprints[ctx.channel.id]
            if curr_sprint.start_timestamp == 0:
                return await ctx.reply("A sprint has been scheduled, but it has not yet started.")
            else:
                return await ctx.reply(
                    f"Sprint of {curr_sprint.duration} minutes was started at"
                    f" <t:{int(curr_sprint.start_timestamp)}>\n"
                    f"Sprint will end in around {curr_sprint.timer.remaining/60:.2f} minutes"
                )
        return

    @sprint.command(
        description="Starts a sprint for the given duration",
        usage="sprint start [duration-min] [wait-min]")
    async def start(self, ctx, duration: int = 15, when: int = 0):
        if not await self.sprint_args_are_valid(ctx, duration, when):
            return
        if await self.is_sprint_ongoing(ctx.channel.id):
            return await ctx.reply("There is already a scheduled/ongoing sprint in this channel.")
        if not await self.sprint_is_confirmed(ctx, duration, when):
            return await ctx.send("Cancelling...")
        else:
            await ctx.send("Sprint confirmed!")
        sprint = Sprint(ctx.channel.id, self.bot, duration)
        self.sprints[ctx.channel.id] = sprint
        await self.wait_until_start(when)
        if ctx.channel.id in self.sprints:
            sprint.start()
            return await self.announce_start(ctx, duration)
        return

    @sprint.command(
        description="Join the ongoing sprint in the channel",
        usage="sprint join [initial-count]")
    async def join(self, ctx, count: int = 0):
        if count < 0:
            return await ctx.reply(YOU_ARE_A_DUMBASS_GIF)
        if not await self.is_sprint_ongoing(ctx.channel.id):
            return await ctx.reply("There are no ongoing sprints in this channel.")
        curr_sprint = self.sprints[ctx.channel.id]
        curr_sprint.add_start_count(ctx.author.id, count)
        return await ctx.reply(
            f"You have successfully joined the sprint with a starting count of {str(count)}!")

    @sprint.command(
        description="Leave the ongoing sprint in the channel",
        usage="sprint leave")
    async def leave(self, ctx):
        if not await self.is_sprint_ongoing(ctx.channel.id):
            return await ctx.reply("There are no ongoing sprints in this channel.")
        curr_sprint = self.sprints[ctx.channel.id]
        if ctx.author.id not in curr_sprint.start_counts:
            return await ctx.reply("You cannot leave a sprint you did not join.")
        curr_sprint.remove_from_sprint(ctx.author.id)
        return await ctx.reply("You have been removed from the sprint.")

    @sprint.command(
        description="Cancels the ongoing sprint in the channel",
        usage="sprint cancel")
    async def cancel(self, ctx):
        if not await self.is_sprint_ongoing(ctx.channel.id):
            return await ctx.reply("There are no ongoing sprints in this channel.")
        curr_sprint = self.sprints[ctx.channel.id]
        curr_sprint.cancel()
        del self.sprints[ctx.channel.id]
        return await ctx.reply("Sprint has been cancelled")

    @sprint.command(
        description="Gives your final count to the bot at the end of a sprint",
        usage="sprint count <final-count>",
        aliases=["finish", "end", "complete"])
    async def count(self, ctx, count: int = 0):
        if not await self.is_sprint_ongoing(ctx.channel.id):
            return await ctx.reply("There are no ongoing sprints in this channel.")
        curr_sprint = self.sprints[ctx.channel.id]
        if ctx.author.id not in curr_sprint.start_counts:
            return await ctx.reply("You were not a participant of this sprint.")
        curr_sprint.add_end_count(ctx.author.id, count)
        return await ctx.message.add_reaction("✅")

    @sprint.command(
        description="Shows a user's total sprinting stats in the server",
        usage="sprint stats <@user>")
    async def stats(self, ctx, user: discord.Member = None):
        if user is None:
            user = ctx.author
        async with ctx.typing():
            sprint_repo = SprintRepository()
            res = sprint_repo.calculate_stats(user.id)
        if int(res['duration']) != 0:
            avg_speed = res['page_count']/res['duration']
        else:
            avg_speed = 0
        return await ctx.reply(
            f"__**{user.display_name}'s Sprint Stats**__\n"
            f"Total Sprints: {res['count']}\n"
            f"Total Duration (in minutes): {res['duration']}\n"
            f"Total Page Count: {res['page_count']}\n"
            f"Avg. Reading Speed: {avg_speed:.2f} pages per minute\n")

    async def is_sprint_ongoing(self, sprint_id):
        return sprint_id in self.sprints

    async def sprint_is_confirmed(self, ctx, duration, when):
        view = Confirm(ctx.author.id)
        await ctx.send(
            f"A Sprint of {duration} minutes will start in {when} minutes. "
            "Please confirm", view=view)
        await view.wait()
        return view.value

    async def announce_start(self, ctx, duration):
        return await ctx.send(
            f"📚📚📚 **SPRINT STARTED: Duration: {duration} minutes** 📚📚📚\n"
            f"To join the sprint, type `{ctx.prefix}sprint join [starting word/page count]`\n"
            f"To leave the sprint, type `{ctx.prefix}sprint leave`\n")

    async def wait_until_start(self, when):
        wait_seconds = 60*when
        await asyncio.sleep(wait_seconds)

    async def sprint_args_are_valid(self, ctx, duration, when):
        if duration <= 0 or duration > 60:
            await ctx.reply("Invalid duration. Sprints can be of at most 60 minutes.")
            return False
        if when < 0 or when > 30:
            await ctx.reply("Invalid wait time. Wait time can be at most 30 minutes.")
            return False
        return True

    def get_participant_mentions(self, curr_sprint):
        mentions = ""
        for user_id in curr_sprint.start_counts.keys():
            mentions += f"<@{str(user_id)}>"
        return mentions

    async def display_sprint_stats(self, sprint_id):
        curr_sprint = self.sprints[sprint_id]
        scores = {}
        for uid in curr_sprint.end_counts.keys():
            scores[uid] = max(0, curr_sprint.end_counts[uid] -
                              curr_sprint.start_counts[uid])
        sorted_scores = [k for k, v in sorted(
            scores.items(), key=lambda item: item[1], reverse=True)]
        msg = "Congratulations sprinters!\n**SPRINT STATS**\n"
        for i, uid in enumerate(sorted_scores):
            reading_speed = scores[uid]/curr_sprint.duration
            msg += f"`{str(i+1)}` <@{uid}>"
            msg += f" - **{str(scores[uid])}** (*{reading_speed:.2f}* per minute)\n"
        channel = self.bot.get_channel(sprint_id)
        return await channel.send(msg)


def setup(bot):
    bot.add_cog(SprintCommands(bot))
