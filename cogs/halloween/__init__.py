"""
The IdleRPG Discord Bot
Copyright (C) 2018-2020 Diniboy and Gelbpunkt

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
import random
import secrets

import discord

from discord.ext import commands

from cogs.shard_communication import user_on_cooldown as user_cooldown
from utils import checks as checks
from utils.i18n import _, locale_doc


class Halloween(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.waiting = None

    @checks.has_char()
    @user_cooldown(43200)
    @commands.command(aliases=["tot"], enabled=False)
    @locale_doc
    async def trickortreat(self, ctx):
        _("""Trick or treat!""")
        waiting = self.waiting
        if not waiting:
            self.waiting = ctx.author
            return await ctx.send(
                _("You walk around the houses... Noone is there... *yet*")
            )
        self.waiting = None
        if secrets.randbelow(2) == 1:
            await ctx.send(
                _(
                    "You walk around the houses and ring at {waiting}'s house! That's a"
                    " trick or treat bag for you, yay!"
                ).format(waiting=waiting)
            )
            await self.bot.pool.execute(
                'UPDATE profile SET trickortreat=trickortreat+1 WHERE "user"=$1;',
                ctx.author.id,
            )
        else:
            await ctx.send(
                _(
                    "You walk around the houses and ring at {waiting}'s house! Sadly"
                    " they don't have anything for you..."
                ).format(waiting=waiting)
            )
        try:
            if secrets.randbelow(2) == 1:
                await waiting.send(
                    "The waiting was worth it: {author} rang! That's a trick or treat"
                    " bag for you, yay!".format(author=ctx.author)
                )
                await self.bot.pool.execute(
                    'UPDATE profile SET trickortreat=trickortreat+1 WHERE "user"=$1;',
                    waiting.id,
                )
            else:
                await waiting.send(
                    "{author} rings at your house, but... Nothing for you!".format(
                        author=ctx.author
                    )
                )
        except discord.Forbidden:
            pass
        async with self.bot.pool.acquire() as conn:
            await conn.execute(
                'UPDATE profile SET money=money+50 WHERE "user"=$1', ctx.author.id
            )
            usr = await conn.fetchval(
                'SELECT "user" FROM profile WHERE "money">=50 AND "user"!=$1 ORDER BY'
                " RANDOM() LIMIT 1;",
                ctx.author.id,
            )
            await conn.execute(
                'UPDATE profile SET money=money-50 WHERE "user"=$1;', usr
            )
        usr = await self.bot.get_user_global(usr) or "Unknown User"
        await ctx.send(
            _("A random stranger nearby, **{user}**, gave you additional $50!").format(
                user=usr
            )
        )

    @checks.has_char()
    @commands.command()
    @locale_doc
    async def yummy(self, ctx):
        _("""Open a trick or treat bag.""")
        # better name?
        if ctx.character_data["trickortreat"] < 1:
            return await ctx.send(
                _("Seems you haven't got a trick or treat bag yet. Go get some!")
            )
        mytry = random.randint(1, 6)
        if mytry == 1:
            minstat, maxstat = 20, 30
        elif mytry == 2 or mytry == 3:
            minstat, maxstat = 10, 19
        else:
            minstat, maxstat = 1, 9
        item = await self.bot.create_random_item(
            minstat=minstat,
            maxstat=maxstat,
            minvalue=1,
            maxvalue=200,
            owner=ctx.author,
            insert=False,
        )
        name = random.choice(
            [
                "Jack's",
                "Spooky",
                "Ghostly",
                "Skeletal",
                "Glowing",
                "Moonlight",
                "Adrian's really awesome",
                "Ghost Buster's",
                "Ghoulish",
                "Vampiric",
                "Living",
                "Undead",
                "Glooming",
            ]
        )
        item["name"] = f"{name} {item['type_']}"
        await self.bot.create_item(**item)
        await self.bot.pool.execute(
            'UPDATE profile SET "trickortreat"="trickortreat"-1 WHERE "user"=$1;',
            ctx.author.id,
        )
        embed = discord.Embed(
            title=_("You gained an item!"),
            description=_("You found a new item when opening a trick-or-treat bag!"),
            color=self.bot.config.primary_colour,
        )
        embed.set_thumbnail(url=ctx.author.avatar_url)
        embed.add_field(name=_("Name"), value=item["name"], inline=False)
        embed.add_field(name=_("Type"), value=item["type_"], inline=False)
        embed.add_field(name=_("Damage"), value=item["damage"], inline=True)
        embed.add_field(name=_("Armor"), value=item["armor"], inline=True)
        embed.add_field(name=_("Value"), value=f"${item['value']}", inline=False)
        embed.set_footer(
            text=_("Remaining trick-or-treat bags: {bags}").format(
                bags=ctx.character_data["trickortreat"] - 1
            )
        )
        await ctx.send(embed=embed)

    @checks.has_char()
    @commands.command(aliases=["totbags", "halloweenbags"])
    async def bags(self, ctx):
        _("""Shows your Trick or Treat Bags.""")
        await ctx.send(
            _(
                "You currently have **{trickortreat}** Trick or Treat Bags, {author}!"
            ).format(
                trickortreat=ctx.character_data["trickortreat"],
                author=ctx.author.mention,
            )
        )


def setup(bot):
    bot.add_cog(Halloween(bot))
