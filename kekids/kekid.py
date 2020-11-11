import logging
import re

import discord
from redbot.core import checks, commands
from redbot.core.commands import BadArgument, Converter
from redbot.core.utils.chat_formatting import humanize_number, pagify
from redbot.core.utils.mod import get_audit_reason, is_allowed_by_hierarchy

_id_regex = re.compile(r"([0-9]{15,21})$")
_mention_regex = re.compile(r"<@!?([0-9]{15,21})>$")


log = logging.getLogger("red.kko-cogs.kekids")


class RawUserIds(Converter):
    async def convert(self, ctx, argument):
        """
        Logic taken from the hackban in core
        """
        if match := _id_regex.match(argument) or _mention_regex.match(argument):
            return int(match.group(1))

        raise BadArgument("{} doesn't look like a valid user ID.".format(argument))


class KekIDs(commands.Cog):
    """Kick a list of IDs from your server"""

    def __init__(self, bot):
        self.bot = bot

    __author__ = "KableKompany#0001"
    __version__ = "1.4.1"

    async def red_delete_data_for_user(self, **kwargs):
        """This cog does not store user data"""
        return

    @commands.command(aliases=["idkek"])
    @commands.guild_only()
    @commands.bot_has_permissions(kick_members=True)
    @checks.admin_or_permissions(kick_members=True)
    async def idkick(
        self,
        ctx: commands.Context,
        user_ids: commands.Greedy[RawUserIds],
        *,
        reason: str = None,
    ):
        """Kick a list of users. Rekt™

        If a reason is specified, it will be the reason that shows up
        in the audit log.
        User IDs need to be provided in order to kick
        using this command
        """
        kicked = []
        errors = {}

        async def show_results():
            text = ("Kicked {num} users from the server.").format(num=humanize_number(len(kicked)))
            if errors:
                text += "\nErrors:\n"
                text += "\n".join(errors.values())

            for p in pagify(text):
                await ctx.send(p)

        user_ids = list(set(user_ids))  # No dupes

        author = ctx.author
        guild = ctx.guild

        if not user_ids:
            await ctx.send_help()
            return

        if not guild.me.guild_permissions.kick_members:
            return await ctx.send("I lack the permissions to do this.")

        for user_id in user_ids:
            user = discord.Object(id=user_id)
            audit_reason = get_audit_reason(author, reason)
            queue_entry = (guild.id, user_id)  # TODO MODLOG INTEGRATION
            if is_allowed_by_hierarchy(guild, mod=ctx.author, user=user):
                try:
                    await guild.kick(user, reason=audit_reason)
                    log.info("{}({}) kicked {}".format(author.name, author.id, user_id))
                except discord.NotFound:
                    errors[user_id] = ("User {user_id} does not exist.").format(user_id=user_id)
                    continue
                except discord.Forbidden:
                    errors[user_id] = ("Could not kick {user_id}: missing permissions.").format(
                        user_id=user_id
                    )
                    continue
                else:
                    kicked.append(user_id)
        await show_results()
