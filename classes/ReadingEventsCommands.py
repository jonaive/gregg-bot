import logging
from abc import abstractmethod

from discord.ext.commands import MemberConverter
from models.EventRepository import EventRepository
from utils.const import EVENT_INT_FIELDS, EVENT_LIST_FIELDS
from utils.views import Confirm, Paginator

from classes.Embeds import EventsListEmbed

logger = logging.getLogger('botlogs')


class ReadingEventsCommands():
    def __init__(self):
        pass

    @abstractmethod
    async def add_announce_reactors(self, payload):
        if self.is_valid_payload(payload, self.announce_channel_id):
            logger.info(f"{payload.user_id} reacted to {payload.message_id}")
            return self.update_event_reactors(
                payload, "announce_id", "$addToSet", "announce_reactors")

    @abstractmethod
    async def remove_announce_reactors(self, payload):
        if self.is_valid_payload(payload, self.announce_channel_id):
            logger.info(f"{payload.user_id} reacted to {payload.message_id}")
            return self.update_event_reactors(
                payload, "announce_id", "$pull", "announce_reactors")

    @abstractmethod
    async def announce(self, ctx, ann_id: int, content):
        event_repo = EventRepository()
        async with ctx.typing():
            event = event_repo.read({"announce_id": ann_id})
            if event is None:
                return await ctx.send("Invalid Announcement Id")
        msg = ""
        for user_id in event["announce_reactors"]:
            msg += f"<@{str(user_id)}> "
        msg_array = [msg]
        if len(content) >= 2000:
            msg_array.append(content.rsplit(". ", 1))
        else:
            msg_array.append(content)
        sent = None
        for msg in msg_array:
            if sent is None:
                sent = await ctx.send(msg)
            else:
                await ctx.send(msg)
        await ctx.message.delete()
        event_repo.update({"announce_id": ann_id}, {"$addToSet": {
                          "announcement_links": sent.jump_url}})
        return

    @abstractmethod
    async def info(self, ctx, ann_id: int):
        async with ctx.typing():
            event_repo = EventRepository()
            event = event_repo.read({"announce_id": ann_id})
            if event is None:
                await ctx.send("Invalid Announcement Id, trying with request id...")
                event = event_repo.read({"request_id": ann_id})
                if event is None:
                    return await ctx.send("Invalid Ids")
            embed = self.EventInfoEmbed()
            embed.create(event)
        return await ctx.reply(embed=embed)

    @abstractmethod
    async def add(self, ctx, ann_id: int, users):
        users = users.split()
        event_repo = EventRepository()
        async with ctx.typing():
            event = event_repo.read({"announce_id": ann_id})
            if event is None:
                return await ctx.send("Invalid Announcement Id")
        converter = MemberConverter()

        event_repo.update({"announce_id": ann_id}, {"$addToSet": {
            "read_by": {"$each": [(await converter.convert(ctx, user)).id for user in users]}}})
        return await ctx.message.add_reaction("✅")

    @abstractmethod
    async def remove(self, ctx, id: int, users):
        users = users.split()
        event_repo = EventRepository()
        converter = MemberConverter()
        async with ctx.typing():
            event = event_repo.read({"announce_id": id})
            if event is None:
                await ctx.send("Invalid Announcement Id, trying with request Id...")
                event = event_repo.read({"request_id": id})
                if event is None:
                    return await ctx.send("Invalid Id")
                else:
                    identifier = {"request_id": id}
            else:
                identifier = {"announce_id": id}

        event_repo.update(identifier, {"$pull": {
            "read_by": {"$in": [(await converter.convert(ctx, user)).id for user in users]}}})
        return await ctx.message.add_reaction("✅")

    @abstractmethod
    async def edit(self, ctx, id: int, field, value):
        if field.lower() in EVENT_INT_FIELDS:
            update = {EVENT_INT_FIELDS[field.lower()]: int(value)}
        elif field.lower() in EVENT_LIST_FIELDS:
            list_delimiter = "|"
            new_vals = [val.strip() for val in value.split(list_delimiter)]
            if field.lower() == "requested_by":
                new_vals = [int(val) for val in value.split(list_delimiter)]
            update = {EVENT_LIST_FIELDS[field.lower()]: new_vals}
        else:
            return await ctx.send("Invalid field")
        event_repo = EventRepository()
        async with ctx.typing():
            event = event_repo.read({"announce_id": id})
            if event is None:
                await ctx.send("Invalid Announcement Id, trying with request Id...")
            else:
                event = event_repo.update(
                    {"announce_id": id}, {"$set": update})
                return await ctx.message.add_reaction("✅")
            event = event_repo.read({"request_id": id})
            if event is None:
                return await ctx.send("Invalid Id")
            else:
                event = event_repo.update({"request_id": id}, {"$set": update})
                return await ctx.message.add_reaction("✅")

    @abstractmethod
    async def delete(self, ctx, id: int):
        event_repo = EventRepository()
        async with ctx.typing():
            event = event_repo.delete({"announce_id": id})
            if event is None:
                await ctx.send("Invalid Announcement Id, trying with request Id...")
            event = event_repo.delete({"request_id": id})
        return await ctx.message.add_reaction("✅")

    def update_event_reactors(self, payload, msg_id_field, oper, reactor_type):
        event_repo = EventRepository()
        event = event_repo.read({msg_id_field: payload.message_id})
        if event is not None:
            return event_repo.update(
                {"_id": event["_id"]}, {oper: {reactor_type: payload.user_id}})

    def is_valid_payload(self, payload, channel_id):
        return payload.user_id != self.bot.user.id and \
            payload.channel_id == channel_id and payload.emoji.name == "✅"

    async def get_reason(self, ctx):
        def check(m):
            return m.channel == ctx.channel and m.author == ctx.author
        await ctx.send(
            "Write something about why you're requesting this book. "
            "Why should other people read this book?",
            delete_after=360)
        try:
            reason_msg = await self.bot.wait_for("message", timeout=360, check=check)
            reason = reason_msg.content
            await reason_msg.delete()
        except Exception as e:
            logger.error(e)
            return None
        return reason

    async def request_is_confirmed(self, ctx, book, req_type):
        view = Confirm(ctx.author.id)
        await ctx.send(
            f"{ctx.author.mention}, you are currently requesting a {req_type} for"
            f" **{book['title']}** by *{book['authors']}*. Please confirm.", delete_after=60,
            view=view)
        await view.wait()
        return view.value

    async def search_events(self, ctx, event_type, query: str):
        async with ctx.typing():
            event_repo = EventRepository()
            events = list(
                event_repo.read_many(
                    {"$text": {"$search": query},
                     "type": event_type},
                    {"score": {"$meta": "textScore"}})
                .sort([("score", {"$meta": "textScore"})]))
            if len(events) == 0:
                return await ctx.send("No results found")
            all_pages = EventsListEmbed.create_many(
                f"Search results for '{query}'", events)
            view = Paginator(all_pages)
            return await ctx.send(embed=all_pages[0], view=view)

    async def list_events(self, ctx, event_type, status, announced=True):
        async with ctx.typing():
            event_repo = EventRepository()
            events = list(event_repo.get_events(event_type, status, announced))
            if len(events) == 0:
                return await ctx.send(f"No {status.title()} events")
            all_pages = EventsListEmbed.create_many(
                f"{status.title()} {event_type}s", events)
            view = Paginator(all_pages)
            return await ctx.send(embed=all_pages[0], view=view)

    async def assign_points(self, ctx, point_type):
        def check(m):
            return m.channel == ctx.channel and m.author == ctx.author
        point_req = await ctx.send(
            f"Enter the points to be given to each {point_type} for the event",
            delete_after=120)
        try:
            point_msg = await self.bot.wait_for(
                "message", timeout=self.timeout_duration, check=check)
            await point_msg.delete()
        except Exception as e:
            logger.error(e)
            return None
        view = Confirm(ctx.author.id)
        await point_req.edit(
            content=f"{point_type} points set to {str(point_msg.content)}.\n"
                    "Please confirm.", view=view)
        await view.wait()
        if view.value is True:
            await point_req.delete()
            return str(point_msg.content)
        else:
            return None

    async def assign_reader_points(self, ctx):
        return await self.assign_points(ctx, "Reader")

    async def confirm_announcement(self, ctx, event_type, embed):
        view = Confirm(ctx.author.id)
        await ctx.send(
            f"{ctx.author.mention}, you are currently announcing a {event_type}. "
            f"This is how the announcement will look like. Please confirm.",
            embed=embed, delete_after=60, view=view)
        await view.wait()
        return view.value
