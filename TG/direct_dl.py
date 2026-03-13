"""
Test Download Command - /test_dl <chapter_url>
This command tests downloading a manga chapter from a URL to verify everything works.
"""
from pyrogram import filters

from bot import Bot, logger

from .storage import retry_on_flood, check_get_web
from Webs.base import EpisodeCard



@Bot.on_message(filters.command("test_dl") & filters.private)
async def test_download_command(client, message):
    """
    Test download command for admins.
    Usage: /test_dl <chapter_url>
    """
    args = message.text.split(maxsplit=1)

    if len(args) < 2:
        return await retry_on_flood(message.reply)(
            "<b>Usage:</b> <code>/test_dl &lt;chapter_url&gt;</code>\n\n"
            "<b>Example:</b>\n"
            "<code>/test_dl https://www.mangamob.com/chapter/en/murim-psychopath-chapter-6-eng-li</code>"
        )

    chapter_url = args[1].strip()
    user_id = message.from_user.id

    # Find the appropriate scraper for this URL
    webs = await check_get_web(chapter_url)
  
    if not webs:
        return await retry_on_flood(message.reply)(
            "<b>❌ Error:</b> Could not find a scraper for this URL.\n"
            f"<b>URL:</b> <code>{chapter_url}</code>"
        )

    sts = await retry_on_flood(message.reply)(
        f"<b>🔍 Testing download...</b>\n\n"
        f"<b>URL:</b> <code>{chapter_url}</code>\n"
        f"<b>Scraper:</b> <code>{webs.__class__.__name__}</code>\n"
        f"<b>Status:</b> <code>Getting pictures...</code>"
    )

    try:
        episodecard = EpisodeCard(
          title="test",
          url=chapter_url,
          anime_title="test",
          data={},
        )
        pictures = await webs.get_downloading_links(episodecard)

        if not pictures:
            return await retry_on_flood(sts.edit)(
                f"<b>❌ Error:</b> No pictures found!\n\n"
                f"<b>URL:</b> <code>{chapter_url}</code>\n"
                f"<b>Scraper:</b> <code>{webs.__class__.__name__}</code>"
            )

        await retry_on_flood(sts.edit)(
            f"Found : {pictures}"
        )


    except Exception as err:
        logger.exception(f"Test download error: {err}")
        await retry_on_flood(sts.edit)(
            f"<b>❌ Error:</b> <code>{str(err)[:500]}</code>"
        )
