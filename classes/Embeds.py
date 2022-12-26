from abc import abstractmethod

import discord
from utils.const import (GOODREADS_LOGO_URL, GOODREADS_PREFIX,
                         GOODREADS_SEARCH_URL, GUILD_ICON_URL, GUILD_NAME,
                         STORYGRAPH_LOGO_URL, STORYGRAPH_PREFIX,
                         STORYGRAPH_SEARCH_URL)


class BookSearchEmbed(discord.Embed):
    def __init__(self, *args, **kwargs):
        kwargs['title'] = "Search Results"
        kwargs['description'] = "No results were found"
        self.set_footer(text=f"Fetched by {kwargs['bot'].user.name}")
        kwargs['colour'] = discord.Color.teal()
        del kwargs['bot']
        super().__init__(*args, **kwargs)


class GoodreadsSearchEmbed(BookSearchEmbed):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def create(self, query, results):
        self.title = f"Search results for '{query}'"
        self.url = GOODREADS_SEARCH_URL.format('+'.join(query.split()))
        self.set_author(name="Goodreads", icon_url=GOODREADS_LOGO_URL)
        if len(results) == 0:
            return
        self.description = ""
        for i, result in enumerate(results):
            title = result["title"]
            authors = result["authors"]
            book_url = result["book_url"]
            book_url = f"{GOODREADS_PREFIX}{book_url}"
            res_str = f"`{str(i+1)}` **[{title}]({book_url})** - *{authors}*\n"
            self.description += res_str
        return


class StorygraphSearchEmbed(BookSearchEmbed):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def create(self, query, results):
        self.title = f"Search results for '{query}'"
        self.url = STORYGRAPH_SEARCH_URL.format('+'.join(query.split()))
        self.set_author(name="StoryGraph", icon_url=STORYGRAPH_LOGO_URL)
        if len(results) == 0:
            return
        self.description = ""
        for i, result in enumerate(results):
            title = result["title"]
            authors = result["authors"]
            book_url = result["book_url"]
            book_url = f"{STORYGRAPH_PREFIX}{book_url}"
            res_str = f"`{str(i+1)}` **[{title}]({book_url})** - *{authors}*\n"
            self.description += res_str
        return


class BookEmbed(discord.Embed):
    def __init__(self, *args, **kwargs):
        del kwargs['bot']
        kwargs['colour'] = discord.Color.teal()
        super().__init__(*args, **kwargs)

    def create(self, book):
        self.title = book['title']
        self.url = book['book_url']
        self.set_author(name=book['authors'], url=book['author_url'])
        self.set_thumbnail(url=book['thumbnail'])


class GoodreadsBookEmbed(BookEmbed):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_footer(
            text=f"Fetched from Goodreads by {kwargs['bot'].user.name}")

    def create(self, book):
        super().create(book)
        if len(book['description']) >= 2000:
            book['description'] = book['description'][:1997] + "..."
        self.description = book['description']
        self.add_field(name="Rating ⭐ ", value="{} ({} ratings)".format(
            book['avg_rating'], book["num_rating"]), inline=True)
        self.add_field(name="Pages 📄 ",
                       value=book['num_pages'], inline=True)
        self.add_field(name="Genres 🔖", value=', '.join(book.get(
            'genres', ["Genres not found"])[:10]), inline=False)
        return


class StorygraphBookEmbed(BookEmbed):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_footer(
            text=f"Fetched from StoryGraph by {kwargs['bot'].user.name}")

    def create(self, book):
        super().create(book)
        self.add_field(name="Content Warnings ⚠️",
                       value=book["content_warnings"], inline=False)
        self.add_field(name="Rating ⭐", value=book.get(
            "avg_rating"), inline=True)
        self.add_field(name="Moods 🤔", value=', '.join(book.get(
            'moods', ["Mood list not found"])[:5]), inline=True)
        self.add_field(name="Pace 🏃‍♂️", value=', '.join(book.get(
            'pace', ["Pace list not found"])[:10]), inline=True)
        for i, question in enumerate(book["questions"]):
            self.add_field(name="🔹 " + question,
                           value=book["answers"][i], inline=False)
        return


class EventRequestEmbed(discord.Embed):
    def __init__(self, *args, **kwargs):
        self.set_footer(text=f"Requested By: {kwargs['requested_by']}")
        kwargs['colour'] = discord.Color.dark_magenta()
        del kwargs['requested_by']
        super().__init__(*args, **kwargs)

    @abstractmethod
    def create(self, event):
        self.title = f"{event['book']['title']} - {event['book']['authors']}"
        self.url = event['book']['book_url']
        self.add_field(name="Request Reason",
                       value=event['reason'], inline=False)
        self.set_thumbnail(url=event['book']['thumbnail'])
        self.add_field(name="Genres", value=', '.join(
            event['book']["genres"]), inline=False)
        self.add_field(name="Pages  📄",
                       value=event['book']["num_pages"], inline=True)
        self.add_field(name="Rating ⭐ ",
                       value=event['book']["avg_rating"], inline=True)


class BRRequestEmbed(EventRequestEmbed):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def create(self, event):
        super().create(event)
        self.set_author(name="BR Request", icon_url=GUILD_ICON_URL)
        self.insert_field_at(1, name="Start Date",
                             value=f"<t:{int(event['start_date'])}:D>", inline=True)
        self.insert_field_at(2, name="End Date",
                             value=f"<t:{int(event['end_date'])}:D>", inline=True)


class MRRequestEmbed(EventRequestEmbed):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def create(self, event):
        super().create(event)
        self.set_author(name="MR Request", icon_url=GUILD_ICON_URL)
        self.description = event['book']['description']
        if len(self.description) > 2000:
            self.description = self.description[:1997] + "..."


class UserEventsListEmbed(discord.Embed):
    def __init__(self, *args, **kwargs):
        kwargs['colour'] = discord.Color.dark_magenta()
        super().__init__(*args, **kwargs)

    @staticmethod
    def create_many(title, events, user_id):
        embed = UserEventsListEmbed(title=title)
        embed.set_author(name=GUILD_NAME, icon_url=GUILD_ICON_URL)
        curr_page = embed
        all_pages = []
        for i, event in enumerate(events):
            i += 1
            genres_string = ', '.join(event['book']['genres'][:3])
            id = event['announce_id']
            if id is None:
                id = event['request_id']
            if event['start_date'] is not None:
                start_date = event["start_date"]
                end_date = event["end_date"]
                if 'channel_id' in event:
                    channel_info_str = f"<#{event['channel_id']}> | "
                else:
                    channel_info_str = ""
                if 'request_reactors' in event and user_id in event['request_reactors']:
                    req_str = "✅"
                else:
                    req_str = "❌"
                if user_id in event['announce_reactors']:
                    ann_str = "✅"
                else:
                    ann_str = "❌"
                if user_id in event['read_by']:
                    read_str = "✅"
                else:
                    read_str = "❌"
                curr_page.add_field(
                    name=f"📕 {event['book']['title']} - {event['book']['authors']}",
                    value=f"{channel_info_str}"
                    f"*[GR Link]({event['book']['book_url']})*\n"
                    f"> __Start Date__: <t:{int(start_date)}:D> | "
                    f"__End Date__: <t:{int(end_date)}:D>\n"
                    f"> __Genres__: {genres_string}\n"
                    f"> __Pages__: {event['book']['num_pages']} | "
                    f"__Rating__: {event['book']['avg_rating']}\n"
                    f"> __Req Reacted__: {req_str} | __Ann Reacted__: {ann_str} | __Read__: {read_str}\n"
                    f"> __ID__: {id}\n\n",
                    inline=False)
            else:
                curr_page.add_field(
                    name=f"📕 {event['book']['title']} - {event['book']['authors']}",
                    value=f"> *[GR Link]({event['book']['book_url']})*\n"
                    f"> __Genres__: {genres_string}\n"
                    f"> __ID__: {id}\n\n",
                    inline=False)
            if i != 1 and i % 5 == 0:
                all_pages.append(curr_page)
                curr_page = EventsListEmbed(title=title)
                curr_page.set_author(name=GUILD_NAME, icon_url=GUILD_ICON_URL)
        if len(events) % 5 != 0:
            all_pages.append(curr_page)
        for page in range(len(all_pages)):
            all_pages[page].set_footer(
                text=f"Use the buttons to flip pages. (Page {page + 1}/{len(all_pages)})")
        return all_pages


class EventsListEmbed(discord.Embed):
    def __init__(self, *args, **kwargs):
        kwargs['colour'] = discord.Color.dark_magenta()
        super().__init__(*args, **kwargs)

    @staticmethod
    def create_many(title, events):
        embed = EventsListEmbed(title=title)
        embed.set_author(name=GUILD_NAME, icon_url=GUILD_ICON_URL)
        curr_page = embed
        all_pages = []
        for i, event in enumerate(events):
            i += 1
            genres_string = ', '.join(event['book']['genres'][:3])
            id = event['announce_id']
            if id is None:
                id = event['request_id']
            if event['start_date'] is not None:
                start_date = event["start_date"]
                end_date = event["end_date"]
                if 'channel_id' in event:
                    channel_info_str = f"<#{event['channel_id']}> | "
                else:
                    channel_info_str = ""
                curr_page.add_field(
                    name=f"📕 {event['book']['title']} - {event['book']['authors']}",
                    value=f"{channel_info_str}"
                    f"*[GR Link]({event['book']['book_url']})*\n"
                    f"> __Start Date__: <t:{int(start_date)}:D> | "
                    f"__End Date__: <t:{int(end_date)}:D>\n"
                    f"> __Genres__: {genres_string}\n"
                    f"> __Pages__: {event['book']['num_pages']} | "
                    f"__Rating__: {event['book']['avg_rating']}\n"
                    f"> __ID__: {id}\n\n",
                    inline=False)
            else:
                curr_page.add_field(
                    name=f"📕 {event['book']['title']} - {event['book']['authors']}",
                    value=f"> *[GR Link]({event['book']['book_url']})*\n"
                    f"> __Genres__: {genres_string}\n"
                    f"> __ID__: {id}\n\n",
                    inline=False)
            if i != 1 and i % 5 == 0:
                all_pages.append(curr_page)
                curr_page = EventsListEmbed(title=title)
                curr_page.set_author(name=GUILD_NAME, icon_url=GUILD_ICON_URL)
        if len(events) % 5 != 0:
            all_pages.append(curr_page)
        for page in range(len(all_pages)):
            all_pages[page].set_footer(
                text=f"Use the buttons to flip pages. (Page {page + 1}/{len(all_pages)})")
        return all_pages


class EventInfoEmbed(discord.Embed):
    def __init__(self, *args, **kwargs):
        kwargs['colour'] = discord.Color.dark_green()
        super().__init__(*args, **kwargs)

    def create(self, event):
        self.set_author(name="Event Stats")
        self.title = f"{event['book']['title']} - {event['book']['authors']}"
        self.url = event['book']['book_url']
        self.add_field(name="Reason", value=event['reason'], inline=False)
        self.add_field(name=f"Read By ({len(event['read_by'])})",
                       value=self.get_formatted_users(event['read_by']), inline=False)
        self.add_field(name=f"Ann reacted By ({len(event['announce_reactors'])})",
                       value=self.get_formatted_users(event['announce_reactors']), inline=False)
        self.set_thumbnail(url=event['book']['thumbnail'])
        self.add_field(name="Genres", value=', '.join(
            event['book']["genres"]), inline=False)
        self.add_field(name="Pages  📄",
                       value=event['book']["num_pages"], inline=True)
        self.add_field(name="Rating ⭐ ",
                       value=event['book']["avg_rating"], inline=True)
        self.add_field(name="Requested By",
                       value=self.get_formatted_users(event["requested_by"]), inline=True)
        try:
            self.add_field(name="Reader Points",
                           value=event['reader_points'], inline=True)
        except Exception:
            pass
        try:
            self.add_field(name="Leader Points",
                           value=event['leader_points'], inline=True)
        except Exception:
            pass
        self.add_field(name="Announcement Links",
                       value=self.get_formatted_links(event), inline=False)
        self.set_footer(text=f"ID: {event['announce_id']}")

    def get_formatted_links(self, event):
        if len(event['announcement_links']) == 0:
            return "None"
        return "\n".join(
            event['announcement_links'])

    def get_formatted_users(self, user_ids):
        if len(user_ids) == 0:
            return "None"
        if len(user_ids) > 40:
            res_str = ', '.join([f"<@{user_id}>" for user_id in user_ids[:40]])
            res_str += " ..."
        else:
            res_str = ', '.join([f"<@{user_id}>" for user_id in user_ids])
        return res_str


class BRInfoEmbed(EventInfoEmbed):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def create(self, event):
        super().create(event)
        self.insert_field_at(
            index=2, name=f"Req reacted By ({len(event['request_reactors'])})",
            value=self.get_formatted_users(event['request_reactors']), inline=False)
        self.insert_field_at(4, name="Start Date",
                             value=f"<t:{int(event['start_date'])}:D>", inline=True)
        self.insert_field_at(5, name="End Date",
                             value=f"<t:{int(event['end_date'])}:D>", inline=True)
        if event['channel_id'] is not None:
            channel_id = int(event['channel_id'])
            self.insert_field_at(6, name="Channel",
                                 value=f"<#{channel_id}>", inline=True)
        self.set_author(name="BR Stats", icon_url=GUILD_ICON_URL)


class MRInfoEmbed(EventInfoEmbed):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def create(self, event):
        super().create(event)
        self.set_author(name="MR Stats", icon_url=GUILD_ICON_URL)


class EventAnnouncementEmbed(discord.Embed):
    def __init__(self, *args, **kwargs):
        self.set_footer(text=f"Requested By: {kwargs['requested_by']}")
        del kwargs['requested_by']
        kwargs['colour'] = discord.Color.purple()
        super().__init__(*args, **kwargs)
        self.set_author(name=GUILD_NAME, icon_url=GUILD_ICON_URL)

    def create(self, event):
        self.title = f"{event['book']['title']} - {event['book']['authors']}"
        self.description = event['book']['description']
        self.url = event['book']['book_url']
        self.set_thumbnail(url=event['book']['thumbnail'])
        self.add_field(name="Start Date",
                       value=f"<t:{int(event['start_date'])}:D>", inline=True)
        self.add_field(name="End Date",
                       value=f"<t:{int(event['end_date'])}:D>", inline=True)
        self.add_field(name="Genres",
                       value=', '.join(event['book']['genres']), inline=False)
        self.add_field(name="Pages 📄 ",
                       value=event['book']['num_pages'], inline=True)
        self.add_field(name="Rating ⭐ ",
                       value=f"{event['book']['avg_rating']} ({event['book']['num_rating']})",
                       inline=True)
        return


class BRAnnouncementEmbed(EventAnnouncementEmbed):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_author(name="Buddy Read", icon_url=GUILD_ICON_URL)


class MRAnnouncementEmbed(EventAnnouncementEmbed):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_author(name="BOTM", icon_url=GUILD_ICON_URL)


class BOTMPollEmbed(discord.Embed):
    def __init__(self, *args, **kwargs):
        kwargs['color'] = discord.Color.dark_purple()
        super().__init__(*args, **kwargs)
        self.reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣',
                          '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
        self.set_author(name=GUILD_NAME, icon_url=GUILD_ICON_URL)
        self.set_thumbnail(url=GUILD_ICON_URL)
        self.title = "What would you like to read for next month?"
        self.set_footer(text="Voting will end in 10 days")

    def create(self, events):
        self.description = ""
        for i, event in enumerate(events):
            self.description += (
                f"{self.reactions[i]} [{event['book']['title']}]({event['book']['book_url']})"
                f" - {event['book']['authors']}\n")
        return


class RecommendationEmbed(discord.Embed):
    def __init__(self, *args, **kwargs):
        self.set_footer(text=f"Recommended By: {kwargs['rec_by']}")
        del kwargs['rec_by']
        kwargs['colour'] = discord.Color.dark_orange()
        super().__init__(*args, **kwargs)

    def create(self, rec):
        self.title = f"{rec['book']['title']} - {rec['book']['authors']}"
        self.url = rec['book']["book_url"]
        self.set_author(name="Recommendation", icon_url=GUILD_ICON_URL)
        self.set_thumbnail(url=rec['book']["thumbnail"])
        self.add_field(name="Recommendation Reason",
                       value=rec["reason"], inline=False)
        self.add_field(name="GR Description",
                       value=rec['book']["description"][:1000], inline=False)
        self.add_field(name="Genres", value=', '.join(
            rec['book']["genres"]), inline=False)
        self.add_field(name="Pages  📄",
                       value=rec['book']["num_pages"], inline=True)
        self.add_field(name="Rating ⭐ ",
                       value=rec['book']["avg_rating"], inline=True)


class ProfileEmbed(discord.Embed):
    def __init__(self, *args, **kwargs):
        if kwargs['thumbnail'] is not None:
            self.set_thumbnail(url=kwargs['thumbnail'])
        self.set_footer(text=f"Fetched by {kwargs['bot'].user.name}")
        del kwargs['thumbnail']
        del kwargs['bot']
        kwargs['color'] = discord.Color.gold()
        super().__init__(*args, **kwargs)

    def create(self, user):
        self.title = f"{user['display_name']}'s Server Profile"
        if "description" in user:
            self.description = user['description']
        if "profile_link" in user:
            self.add_field(name="GR/SG Link",
                           value=user['profile_link'], inline=False)
        if "curr_reading" in user:
            self.add_field(name="Reading", value=self.get_formatted_list(
                user["curr_reading"]), inline=True)
        if "top_genres" in user:
            self.add_field(name="Top Genres", value=self.get_formatted_list(
                user["top_genres"]), inline=True)
        if "top_authors" in user:
            self.add_field(name="Top Authors", value=self.get_formatted_list(
                user["top_authors"]), inline=True)
        self.set_author(name=GUILD_NAME, icon_url=GUILD_ICON_URL)
        return

    def get_formatted_list(self, values):
        val = "\n".join([f"`{str(i+1)}` {val}" for i,
                        val in enumerate(values)])
        if val == "":
            return "N/A"
        return val


class InactiveUsersEmbed(discord.Embed):
    def __init__(self, *args, **kwargs):
        kwargs['color'] = discord.Color.red()
        super().__init__(*args, **kwargs)
        self.title = "Inactive Users"
        self.description = ""

    def create(self, users):
        for user in users:
            if "last_message_at" not in user or user["last_message_at"] is None:
                self.description += f"<@{user['id']}>: 0 messages\n"
            else:
                self.description += f"<@{user['id']}>: <t:{int(user['last_message_at'])}:R>\n"


class ReaderboardEmbed(discord.Embed):
    def __init__(self, *args, **kwargs):
        kwargs['color'] = discord.Color.blue()
        self.title = "Reading Leaderboard"
        super().__init__(*args, **kwargs)

    @staticmethod
    def create_many(users):
        all_pages = []
        chunk = 10
        user_lists = [users[i:i+chunk] for i in range(0, len(users), chunk)]
        i = 1
        for users in user_lists:
            embed = ReaderboardEmbed(description="")
            embed.set_author(name=GUILD_NAME, icon_url=GUILD_ICON_URL)
            curr_page = embed
            for result in users:
                user_id = result[0]
                score = result[1]
                curr_page.description += f"{str(i)}) <@{str(user_id)}> --> **{str(score)}**\n"
                i += 1
            all_pages.append(curr_page)
        for page in range(len(all_pages)):
            all_pages[page].set_footer(
                text=f"Use the buttons to flip pages. (Page {page + 1}/{len(all_pages)})")
        return all_pages


class QotdSuggestionEmbed(discord.Embed):
    def __init__(self, *args, **kwargs):
        kwargs['color'] = discord.Color.blurple()
        super().__init__(*args, **kwargs)

    def create(self, content):
        author = content['author']
        suggestion = content['suggestion']
        self.title = f"QOTD Suggestion by {author.display_name}"
        self.description = suggestion
        self.set_author(name=author.display_name, url=author.avatar.url)
        return
