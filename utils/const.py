# Bot
PREFIX = "!"
OWNERS = [811182966046064660]
GUILD_NAME = "Organized Book Club"
GUILD_ICON_URL = ("https://cdn.discordapp.com/icons/811077227449286667/"
                  "a_49fdc481fabe8bac57bf05b667e920c2.gif?size=4096")
JOIN_MESSAGE = "I have arrived!"
ACTIVITY = "discord.gg/BookClubs"
ACTIVITY_TYPE = "playing"
STATUS_TYPE = "online"

# Goodreads
GOODREADS_PREFIX = "https://goodreads.com"
GOODREADS_LOGO_URL = (
    "http://d.gr-assets.com/misc/"
    "1454549143-1454549143_goodreads_misc.png")
GOODREADS_SEARCH_URL = GOODREADS_PREFIX + \
    "/search?utf8=✓&query={}&search_type=books"
GOODREADS_QUOTES_URL = GOODREADS_PREFIX + "/quotes"

# Storygraph
STORYGRAPH_PREFIX = "https://app.thestorygraph.com/"
STORYGRAPH_LOGO_URL = (
    "https://app.thestorygraph.com/"
    "assets/logo-no-text-c4ee077e55eff96a040071bb24d583360e2b52ed96e293a0768c6ba2384bf82c.png")
STORYGRAPH_SEARCH_URL = STORYGRAPH_PREFIX + \
    "browse?utf8=✓&button=&search_term={}"

# QOTD
QOTD_SUGGESTION_CHANNEL = 819813715758678026
QOTD_SEND_CHANNEL = 814032519157907506
QOTD_MENTION_ROLE = 819801641091203093


# Help
HELP_COGS = [
    "Users",
    "Goodreads",
    "StoryGraph",
    "Buddy Reads",
    "Monthly Reads",
    "Readerboard",
    "Sprints",
    "Qotd",
]

# Reading Events
EVENT_INT_FIELDS = {
    "start_date": "start_date",
    "end_date": "end_date",
    "announce_id": "announce_id",
    "request_id": "request_id",
    "channel_id": "channel_id",
    "reader_points": "reader_points",
    "leader_points": "leader_points",
}
EVENT_LIST_FIELDS = {
    "requested_by": "requested_by",
    "announcement_links": "announcement_links",
}
# Buddy Reads
BR_ANNOUNCEMENT_CHANNEL_ID = 811210272298500096
BR_REQUEST_CHANNEL_ID = 825098973417177128

# Monthly Reads
MR_ANNOUNCEMENT_CHANNEL_ID = 811100856702861312
MR_READING_CHANNEL_ID = 811108641859305542
MR_FINISHED_CHANNEL_ID = 811108678135447573
READING_EVENTS_ROLE_ID = 817979188010025000

# Sprints
YOU_ARE_A_DUMBASS_GIF = (
    "https://tenor.com/view/"
    "brooklyn-nine-nine-test-results-dumb-dumbass-you-are-so-stupid-gif-14192289")
# Users
PROFILE_STRING_FIELDS = {
    "about": "description",
    "goodreads": "profile_link",
    "gr": "profile_link",
    "link": "profile_link",
    "storygraph": "profile_link",
    "sg": "profile_link"
}
PROFILE_LIST_FIELDS = {
    "reading": "curr_reading",
    "genres": "top_genres",
    "authors": "top_authors",
}

# Disboard Logging
DISBOARD_BOT_ID = 302050872383242240
BUMP_CHANNEL_ID = 811103146355982336
