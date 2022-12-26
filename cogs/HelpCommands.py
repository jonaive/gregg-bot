import logging

import discord
from discord.ext import commands
from utils.const import HELP_COGS, OWNERS
from utils.views import Paginator

logger = logging.getLogger('botlogs')


class HelpCommands(commands.Cog, name="Help"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        description="Shows the help menu or information for a specific command when specified.",
        usage="help [command]",
        aliases=["h", "commands"],
    )
    async def help(self, ctx, *, query: str = None):
        bot_user = self.bot.user
        if query:
            return await self.get_help_for_query(ctx, query, bot_user)
        else:
            return await self.get_full_help_menu(ctx, bot_user)

    async def get_help_for_query(self, ctx, query, bot_user):
        if self.bot.get_command(query.lower()):
            command = self.bot.get_command(query.lower())
            embed = await self.create_page_for_command(ctx, command)
            return await ctx.send(embed=embed)
        elif self.bot.get_cog(query):
            cog = self.bot.get_cog(query)
            template = await self.get_help_page_template(ctx, bot_user)
            page = await self.create_page_for_cog(cog, template)
            return await ctx.send(embed=page)
        else:
            e = discord.Embed(description=f"That command does not exist. \
                Use `{ctx.prefix}help` to see all the commands.",)
            return await ctx.send(embed=e)

    async def get_full_help_menu(self, ctx, bot_user):
        all_pages = []
        page = await self.create_first_page_embed(bot_user)
        all_pages.append(page)

        for cog_name in HELP_COGS:
            cog = self.bot.get_cog(cog_name)
            template = await self.get_help_page_template(ctx, bot_user)
            page = await self.create_page_for_cog(cog, template)
            all_pages.append(page)

        for page in range(len(all_pages)):
            all_pages[page].set_footer(
                text=f"Use the buttons to flip pages. (Page {page + 1}/{len(all_pages)})")
        view = Paginator(all_pages)
        return await ctx.send(embed=all_pages[0], view=view)

    async def create_page_for_command(self, ctx, command):
        embed = discord.Embed(title=command.usage, color=discord.Color.greyple(
        ), description=command.description)
        usage = "\n".join([ctx.prefix + x.strip()
                          for x in command.usage.split("\n")])
        embed.add_field(name="Usage", value=f"```{usage}```", inline=False)

        if len(command.aliases) > 1:
            embed.add_field(
                name="Aliases", value=f"`{'`, `'.join(command.aliases)}`")
        elif len(command.aliases) > 0:
            embed.add_field(name="Alias", value=f"`{command.aliases[0]}`")
        return embed

    async def create_first_page_embed(self, bot_user):
        page = discord.Embed(
            color=discord.Color.greyple(),
            title=f"{bot_user.name} Help Menu",
            description=(
                f"{self.bot.user.name} is a feature-rich Discord bot designed to "
                "enhance the experience in a book club server."
                " It is a personal project, and is not publically available. "
                f"If you're having trouble, please contact <@{OWNERS[0]}>"
                "in the **[Organized Book Club](https://discord.gg/BookClubs)** server."))
        page.set_thumbnail(url=bot_user.avatar.url)
        page.set_footer(text="Use the reactions to flip pages.")
        return page

    async def create_page_for_cog(self, cog, page):
        for cmd in cog.walk_commands():
            page.add_field(
                name=cmd.usage, value=cmd.description, inline=False)
        return page

    async def get_help_page_template(self, ctx, bot_user):
        template = discord.Embed(
            color=discord.Color.greyple(),
            description=f"My prefix is `{ctx.prefix}`. \
                Use `{ctx.prefix}help <command>` for more information on a command.",
        )
        template.set_author(
            name=f"{bot_user.name} Help Menu", icon_url=bot_user.avatar.url)
        template.set_thumbnail(url=bot_user.avatar.url)
        template.set_footer(text="Use the reactions to flip pages.")
        return template


def setup(bot):
    bot.add_cog(HelpCommands(bot))
