import logging
from datetime import datetime
from typing import Union

import discord
from classes.Embeds import BRAnnouncementEmbed, BRInfoEmbed, BRRequestEmbed
from classes.ReadingEventsCommands import ReadingEventsCommands
from discord.ext import commands
from discord.ext.commands.core import guild_only, has_any_role, has_role
from models.EventRepository import EventRepository
from utils import tools
from utils.const import (BR_ANNOUNCEMENT_CHANNEL_ID, BR_REQUEST_CHANNEL_ID,
                         PREFIX, READING_EVENTS_ROLE_ID)
from utils.views import Confirm

logger = logging.getLogger('botlogs')


class BuddyReadsCommands(commands.Cog, ReadingEventsCommands, name="Buddy Reads"):
    def __init__(self, bot):
        self.bot = bot
        self.timeout_duration = 120
        self.announce_channel_id = BR_ANNOUNCEMENT_CHANNEL_ID
        self.request_channel_id = BR_REQUEST_CHANNEL_ID
        self.EventInfoEmbed = BRInfoEmbed
        self.EventAnnouncementEmbed = BRAnnouncementEmbed

    @commands.Cog.listener("on_raw_reaction_add")
    async def add_request_reactors(self, payload):
        if self.is_valid_payload(payload, self.request_channel_id):
            logger.info(f"{payload.user_id} reacted to {payload.message_id}")
            return self.update_event_reactors(
                payload, "request_id", "$addToSet", "request_reactors")

    @commands.Cog.listener("on_raw_reaction_remove")
    async def remove_request_reactors(self, payload):
        if self.is_valid_payload(payload, self.request_channel_id):
            logger.info(f"{payload.user_id} unreacted to {payload.message_id}")
            return self.update_event_reactors(
                payload, "request_id", "$pull", "request_reactors")

    @commands.Cog.listener("on_raw_reaction_add")
    async def add_announce_reactors(self, payload):
        return await super().add_announce_reactors(payload)

    @commands.Cog.listener("on_raw_reaction_remove")
    async def remove_announce_reactors(self, payload):
        return await super().remove_announce_reactors(payload)

    @commands.group(description="Shows the various subcommands related to BRs", usage="br", case_insensitive=True)
    @guild_only()
    @commands.cooldown(rate=1, per=1.5, type=commands.BucketType.user)
    async def br(self, ctx):
        if ctx.invoked_subcommand is None:
            return await ctx.reply(
                "__**BR Commands**__\n"
                f"`{PREFIX}br request <goodreads-link>` to request a BR\n"
                f"`{PREFIX}br list <fin|ongoing|upcoming>` to get a list of BRs\n"
                f"`{PREFIX}br info <announcement-msg-id>` to get stats of a particular BR\n")
        return

    @br.command(
        name="request",
        description="Starts the process to request a Buddy Read on the server",
        usage="br request <goodreads-url>",
        aliases=["req"])
    @commands.cooldown(rate=1, per=1.5, type=commands.BucketType.user)
    async def request(self, ctx, url: tools.clean_url):
        if not tools.is_valid_url(url):
            return await ctx.send("Invalid URL, cancelling...", delete_after=60)
        if not await self.user_has_agreed(ctx):
            return await ctx.send("Cancelling...", delete_after=60)
        async with ctx.typing():
            book = await tools.get_book_from_url(url)

        if not await self.request_is_confirmed(ctx, book, "Buddy Read"):
            return await ctx.send("Cancelling...", delete_after=60)
        reason = await self.get_reason(ctx)
        start_date = await self.get_date_from_input(ctx, "Start Date")
        if start_date is None:
            return await ctx.send("Date not processed. Cancelling...", delete_after=60)
        end_date = await self.get_date_from_input(ctx, "End Date")
        if end_date is None:
            return await ctx.send("Date not processed. Cancelling...", delete_after=60)
        event = {
            "book": book,
            "type": "BR",
            "start_date": start_date, "end_date": end_date,
            "requested_by": [ctx.author.id], "read_by": [],
            "announce_id": None, "request_id": None,
            "reason": reason,
            "channel_id": None,
            "request_reactors": [], "announce_reactors": [],
            "reader_points": 0, "leader_points": 0,
            "announcement_links": []
        }
        event_repo = EventRepository()
        result = event_repo.insert(event)
        if result.acknowledged is False:
            return await ctx.send("Error inserting event to db. Cancelling...", delete_after=60)
        embed = BRRequestEmbed(requested_by=ctx.author.display_name)
        embed.create(event)
        sent = await ctx.send(embed=embed)
        event_repo.update(
            {"_id": result.inserted_id}, {"$set": {"request_id": sent.id}})
        await ctx.message.delete()
        return await sent.add_reaction("✅")

    @br.group(
        name='search', description="Searches BRs with the query term",
        aliases=["find"],
        usage="br search <query>", case_insensitive=True)
    async def search(self, ctx, *, query):
        return await self.search_events(ctx, "BR", query)

    @br.group(
        name="list", description="Shows the BR list", aliases=["show"], case_insensitive=True)
    @commands.cooldown(rate=1, per=1.5, type=commands.BucketType.user)
    async def list(self, ctx):
        if ctx.invoked_subcommand is None:
            return await self.list_events(ctx, "BR", "present")
        return

    @list.command(
        name="finished", description="Shows the past BRs",
        usage="br list finished", aliases=["fin", "past"])
    async def list_past(self, ctx):
        return await self.list_events(ctx, "BR", "past")

    @list.command(
        name="present", description="Shows the present BRs",
        usage="br list present", aliases=["curr", "ongoing"])
    async def list_present(self, ctx):
        return await self.list_events(ctx, "BR", "present")

    @list.command(
        name="future", description="Shows the upcoming BRs",
        usage="br list future", aliases=["next", "fut", "upcoming"])
    async def list_future(self, ctx):
        return await self.list_events(ctx, "BR", "future")

    @list.command(
        name="requested", description="Shows the requested BRs",
        usage="br list requested", aliases=["incomplete", "req"])
    async def list_requested(self, ctx):
        return await self.list_events(ctx, "BR", "future", announced=False)

    @br.command(name="approve",
                description="[Staff] Approve and make announcement for a BR",
                usage="br approve <req-id> <#channel/#thread>", aliases=["allow", "ap"])
    @has_role("Staff")
    async def approve(self, ctx, req_id: int, channel: Union[discord.TextChannel, discord.Thread]):
        event_repo = EventRepository()
        async with ctx.typing():
            event = event_repo.read({"request_id": req_id})
            if event is None:
                return await ctx.send("Invalid BR Request Id")

        reader_points = await self.assign_reader_points(ctx)
        if reader_points is None:
            return await ctx.send("Cancelling...")
        leader_points = await self.assign_leader_points(ctx)
        if leader_points is None:
            return await ctx.send("Cancelling...")

        async with ctx.typing():
            user = await self.bot.fetch_user(event['requested_by'][0])
            embed = self.EventAnnouncementEmbed(requested_by=user.display_name)
            embed.create(event)
            if not await self.confirm_announcement(ctx, "Buddy Read", embed):
                return await ctx.send("Cancelling...", delete_after=60)
            ann_channel = self.bot.get_channel(self.announce_channel_id)
            msg = await ann_channel.send(
                f"<@&{READING_EVENTS_ROLE_ID}> New Buddy Read! "
                f"Please react with ✅ if you'd like to participate in the discussions.\n"
                f"Discussion will take place in {channel.mention}",
                embed=embed)
            event_repo.update({"_id": event["_id"]}, {"$set": {
                "announce_id": int(msg.id),
                "channel_id": int(channel.id),
                "reader_points": int(reader_points),
                "leader_points": int(leader_points)}})
        await msg.add_reaction("✅")
        return await msg.publish()

    @br.command(name="announce",
                description="Broadcasts a message by pinging participants of a BR",
                usage="br announce <id> <message>", aliases=["broadcast", "ping", "an"])
    @has_any_role("Staff", "BR Leader")
    async def announce(self, ctx, ann_id: int, *, content):
        return await super().announce(ctx, ann_id, content)

    @br.command(name="info",
                description="Shows the stats for a particular BR",
                usage="br info <id>", aliases=["stats"])
    async def info(self, ctx, ann_id: int):
        return await super().info(ctx, ann_id)

    @br.command(name="add",
                description="[Staff] Add members who've participated and discussed in a BR",
                usage="br add <id> @user1 @user2 ...", aliases=["assign"])
    @has_role("Staff")
    async def add(self, ctx, ann_id: int, *, users):
        return await super().add(ctx, ann_id, users)

    @br.command(name="remove",
                description="[Staff] Remove members who've participated and discussed in a BR",
                usage="br remove <id> @user1 @user2 ...", aliases=["unassign"])
    @has_role("Staff")
    async def remove(self, ctx, ann_id: int, *, users):
        return await super().remove(ctx, ann_id, users)

    @br.command(name="edit",
                description="[Staff] Edits a BR",
                usage="br edit <id> <field> <value>", aliases=["change", "update"])
    @has_role("Staff")
    async def edit(self, ctx, id: int, field, *, value):
        return await super().edit(ctx, id, field, value)

    @br.command(name="delete",
                description="[Staff] Deletes a BR",
                usage="br delete <id>", aliases=["purge"])
    @has_role("Staff")
    async def delete(self, ctx, id: int):
        return await super().delete(ctx, id)

    async def user_has_agreed(self, ctx):
        view = Confirm(ctx.author.id)
        await ctx.send(
            "**Read before proceeding**\n"
            "Please note that a server buddy read is not simply a read-along request,"
            " it includes several responsibilities as well. "
            "You will be expected to monitor, moderate and promote qualitative discussions "
            "throughout the duration of the buddy read.\n"
            "If you don't have time or you're unable to put this effort in your chosen duration, "
            "you can cancel this request, and have a more casual"
            "read-along with others if you prefer. However, "
            "you will get reader points for offical BRs only", view=view, delete_after=180)
        await view.wait()
        return view.value

    @br.command(description="[Staff] Refreshes a BRs reactions from the announcement msg",
                usage="br refresh <id>")
    @has_role("Staff")
    async def refresh(self, ctx, id: int):
        event_repo = EventRepository()
        async with ctx.typing():
            event = event_repo.read({"announce_id": id})
            if event is None:
                await ctx.send("Invalid Announcement Id, trying with request Id...")
                event = event_repo.read({"request_id": id})
                if event is None:
                    return await ctx.send("Invalid Id")
        ann_channel = self.bot.get_channel(self.announce_channel_id)
        msg = await ann_channel.fetch_message(id)
        all_reactions = msg.reactions
        reactors = []
        for reaction in all_reactions:
            if reaction.emoji == "✅":
                async for user in reaction.users():
                    if user.bot is False:
                        reactors.append(user.id)
        event_repo.update({"announce_id": id}, {
                          "$set": {"announce_reactors": reactors}})
        return

    async def get_date_from_input(self, ctx, date_type):
        def check(m):
            return m.channel == ctx.channel and m.author == ctx.author
        dateReq = await ctx.send(
            f"Enter the **{date_type}** "
            f"for the event in **YYYY-MM-DD** format:",
            delete_after=120)
        # TODO: Add better parsing for handling of different formats
        try:
            dateMsg = await self.bot.wait_for("message", timeout=self.timeout_duration, check=check)
            await dateMsg.delete()
            date_obj = datetime.strptime(str(dateMsg.content), "%Y-%m-%d")
        except Exception as e:
            logger.error(e)
            return None
        view = Confirm(ctx.author.id)
        await dateReq.edit(
            content="{} set as {:%d, %b %Y}. "
                    "Please confirm.".format(date_type, date_obj), view=view)
        await view.wait()
        if view.value is True:
            await dateReq.delete()
            return date_obj.timestamp()
        else:
            return None

    async def assign_leader_points(self, ctx):
        return await self.assign_points(ctx, "Leader")


def setup(bot):
    bot.add_cog(BuddyReadsCommands(bot))
