import calendar
import datetime
import logging
import random

from classes.Embeds import (BOTMPollEmbed, MRAnnouncementEmbed, MRInfoEmbed,
                            MRRequestEmbed)
from classes.ReadingEventsCommands import ReadingEventsCommands
from discord.ext import commands
from discord.ext.commands.core import guild_only, has_role
from models.EventRepository import EventRepository
from utils import tools
from utils.const import (MR_ANNOUNCEMENT_CHANNEL_ID, MR_FINISHED_CHANNEL_ID,
                         MR_READING_CHANNEL_ID, PREFIX, READING_EVENTS_ROLE_ID)

logger = logging.getLogger('botlogs')


class MonthlyReadsCommands(commands.Cog, ReadingEventsCommands, name="Monthly Reads"):
    def __init__(self, bot):
        self.bot = bot
        self.timeout_duration = 120
        self.announce_channel_id = MR_ANNOUNCEMENT_CHANNEL_ID
        self.EventInfoEmbed = MRInfoEmbed
        self.EventAnnouncementEmbed = MRAnnouncementEmbed

    @commands.Cog.listener("on_raw_reaction_add")
    async def add_announce_reactors(self, payload):
        return await super().add_announce_reactors(payload)

    @commands.Cog.listener("on_raw_reaction_remove")
    async def remove_announce_reactors(self, payload):
        return await super().remove_announce_reactors(payload)

    @commands.group(description="Shows the various subcommands for MRs", usage="mr", case_insensitive=True)
    @guild_only()
    async def mr(self, ctx):
        if ctx.invoked_subcommand is None:
            return await ctx.reply(
                "__**BR Commands**__\n"
                f"`{PREFIX}mr request <goodreads-link>` to request a MR/BOTM\n"
                f"`{PREFIX}mr list <fin|ongoing|upcoming>` to get a list of MRs\n"
                f"`{PREFIX}mr info <announcement-msg-id>` to get stats of a particular MR\n")
        return

    @mr.command(
        name="request",
        description="Starts the process to request a Monthly Read on the server",
        usage="mr request <goodreads-url>",
        aliases=["req"])
    @commands.cooldown(rate=1, per=1.5, type=commands.BucketType.user)
    async def request(self, ctx, url: tools.clean_url):
        if not tools.is_valid_url(url):
            return await ctx.send("Invalid URL, cancelling...", delete_after=60)
        event_repo = EventRepository()
        async with ctx.typing():
            event = event_repo.read(
                {"type": "MR", "announce_id": None, "book.book_url": url})
            if event is not None:
                event_repo.update({"type": "MR", "announce_id": None, "book.book_url": url}, {
                                  "$addToSet": {"requested_by": ctx.author.id}})
                return await ctx.reply("This book has already been requested!")

            book = await tools.get_book_from_url(url)

        if not await self.request_is_confirmed(ctx, book, "Monthly Read"):
            return await ctx.send("Cancelling...", delete_after=60)
        reason = await self.get_reason(ctx)
        event = {
            "book": book,
            "type": "MR",
            "requested_by": [ctx.author.id], "read_by": [],
            "announce_id": None, "request_id": None,
            "start_date": None, "end_date": None,
            "reason": reason,
            "announce_reactors": [],
            "reader_points": 0,
            "announcement_links": []
        }
        result = event_repo.insert(event)
        if result.acknowledged is False:
            return await ctx.send("Error inserting event to db. Cancelling...", delete_after=60)
        embed = MRRequestEmbed(requested_by=ctx.author.display_name)
        embed.create(event)
        sent = await ctx.send(embed=embed)
        event_repo.update(
            {"_id": result.inserted_id}, {"$set": {"request_id": sent.id}})
        await ctx.message.delete()
        return await sent.add_reaction("✅")

    @mr.group(
        name='search', description="Searches MRs with the query term",
        aliases=["find"],
        usage="mr search <query>", case_insensitive=True)
    async def search(self, ctx, *, query):
        return await self.search_events(ctx, "MR", query)

    @mr.group(
        name="list", description="Shows the MR list", aliases=["show"], case_insensitive=True)
    @commands.cooldown(rate=1, per=1.5, type=commands.BucketType.user)
    async def list(self, ctx):
        if ctx.invoked_subcommand is None:
            return await self.list_events(ctx, "MR", "present")
        return

    @list.command(
        name="finished", description="Shows the past BRs",
        usage="mr list finished", aliases=["fin", "past"])
    async def list_past(self, ctx):
        return await self.list_events(ctx, "MR", "past")

    @list.command(
        name="present", description="Shows the present MRs",
        usage="mr list present", aliases=["curr", "ongoing"])
    async def list_present(self, ctx):
        return await self.list_events(ctx, "MR", "present")

    @list.command(
        name="future", description="Shows the upcoming MRs",
        usage="mr list future", aliases=["next", "fut", "upcoming"])
    async def list_future(self, ctx):
        return await self.list_events(ctx, "MR", "future")

    @list.command(
        name="requested", description="Shows the requested MRs",
        usage="mr list requested", aliases=["incomplete", "req"])
    async def list_requested(self, ctx):
        return await self.list_events(ctx, "MR", "requested", announced=False)

    @mr.command(name="approve",
                description="[Staff] Approve and make announcement for a MR",
                usage="mr approve <req-id> <#channel/#thread>", aliases=["allow", "ap"])
    @has_role("Staff")
    async def approve(self, ctx, req_id: int):
        event_repo = EventRepository()
        async with ctx.typing():
            event = event_repo.read({"request_id": req_id})
            if event is None:
                return await ctx.send("Invalid Request Id")

        reader_points = await self.assign_reader_points(ctx)
        if reader_points is None:
            return await ctx.send("Cancelling...")
        curr_date = datetime.datetime.utcnow()
        if(curr_date.month == 12):
            next_month_last_date = calendar.monthrange(
            curr_date.year + 1, 1)[1]
            start_date = datetime.datetime(
                curr_date.year + 1, 1, 1).timestamp()
            end_date = datetime.datetime(
                curr_date.year+1, 1, next_month_last_date).timestamp()
        else:
            next_month_last_date = calendar.monthrange(
                curr_date.year, curr_date.month+1)[1]
            start_date = datetime.datetime(
                curr_date.year, curr_date.month+1, 1).timestamp()
            end_date = datetime.datetime(
                curr_date.year, curr_date.month+1, next_month_last_date).timestamp()
        print(start_date, end_date)
        async with ctx.typing():
            user = await self.bot.fetch_user(event['requested_by'][0])
            embed = self.EventAnnouncementEmbed(requested_by=user.display_name)
            event['start_date'] = start_date
            event['end_date'] = end_date
            embed.create(event)
            if not await self.confirm_announcement(ctx, "Monthly Read", embed):
                return await ctx.send("Cancelling...", delete_after=60)
            ann_channel = self.bot.get_channel(self.announce_channel_id)
            msg = await ann_channel.send(
                f"<@&{READING_EVENTS_ROLE_ID}> New BOTM! "
                f"Please react with ✅ if you'd like to participate in the discussions.\n"
                f"Discussion will take place in "
                f"<#{MR_READING_CHANNEL_ID}> and <#{MR_FINISHED_CHANNEL_ID}>",
                embed=embed)
            event_repo.update({"_id": event["_id"]}, {"$set": {
                "start_date": int(start_date), "end_date": int(end_date),
                "announce_id": int(msg.id),
                "reader_points": int(reader_points)}})
        await msg.add_reaction("✅")
        return await msg.publish()

    @mr.command(name="announce",
                description="Broadcasts a message by pinging participants of a MR",
                usage="mr announce", aliases=["broadcast", "ping", "an"])
    @has_role("Staff")
    async def announce(self, ctx, ann_id: int, *, content):
        return await super().announce(ctx, ann_id, content)

    @mr.command(name="info",
                description="Shows the stats for a particular MR",
                usage="mr info <id>", aliases=["stats"])
    async def info(self, ctx, ann_id: int):
        return await super().info(ctx, ann_id)

    @has_role("Staff")
    @mr.command(name="add",
                description="Add members who've participated and discussed in a MR",
                usage="mr add <id> @user1 @user2 ...", aliases=["assign"])
    async def add(self, ctx, ann_id: int, *, users):
        return await super().add(ctx, ann_id, users)

    @mr.command(name="remove",
                description="Remove members who've participated and discussed in a MR",
                usage="mr remove <id> @user1 @user2 ...", aliases=["unassign"])
    @has_role("Staff")
    async def remove(self, ctx, ann_id: int, *, users):
        return await super().remove(ctx, ann_id, users)

    @mr.command(name="random",
                description="Shows a random selection from the requested MRs",
                usage="mr random [num]")
    @has_role("Staff")
    async def random(self, ctx, k=5):
        async with ctx.typing():
            event_repo = EventRepository()
            events = list(event_repo.read_many(
                {"type": "MR", "announce_id": None}))
            events = random.choices(events, k=k)
            content = ""
            for event in events:
                content += f"**{event['book']['title']}** - *{event['book']['authors']}*\n"
                content += f"> Genres: {event['book']['genres']}\n"
                content += f"> Id: {event['request_id']}\n"
        return await ctx.reply(content)

    @mr.command(name="poll",
                description="Create a poll for the BOTM",
                usage="mr poll <id1> <id2> <id3> ...")
    @has_role("Staff")
    async def poll(self, ctx, *, content):
        id_strs = content.split(' ')
        async with ctx.typing():
            event_repo = EventRepository()
            events = []
            for eid in id_strs:
                event = event_repo.read({"request_id": int(eid)})
                if event is None:
                    return await ctx.reply(f"{eid} is not a valid request Id")
                events.append(event)
        embed = BOTMPollEmbed()
        embed.create(events)
        channel = self.bot.get_channel(MR_ANNOUNCEMENT_CHANNEL_ID)
        reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣',
                     '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
        msg = await channel.send(f"<@&{READING_EVENTS_ROLE_ID}> Vote for the next BOTM!", embed=embed)
        for reaction in reactions[:len(events)]:
            await msg.add_reaction(reaction)
        return await msg.publish()

    @mr.command(name="edit",
                description="Edits a MR",
                usage="mr edit <id> <field> <value>", aliases=["change", "update"])
    @has_role("Staff")
    async def edit(self, ctx, id: int, field, *, value):
        return await super().edit(ctx, id, field, value)

    @mr.command(name="delete",
                description="Deletes a MR",
                usage="mr delete <id>", aliases=["purge"])
    @has_role("Staff")
    async def delete(self, ctx, id: int):
        return await super().delete(ctx, id)


def setup(bot):
    bot.add_cog(MonthlyReadsCommands(bot))
