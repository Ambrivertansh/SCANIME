from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from pyrogram.errors import FloodWait
from .storage import *
import asyncio

from Tools.db import add_user 

from bot import Bot, Vars

from aioitertools.itertools import islice

logger = get_logger(__name__)

episode_cache = {} # anime_url_unqiue: AnimeClass
episode_len = 40

class Downloading_:
  """ This storage practular downloading links """
  __slots__ = ("download_link", "quality", "anime_title", "title", "webs_data", "sts")
  def __init__(self, download_link, quality, anime_title, title, webs_data, sts=None):
    self.anime_title: str = anime_title
    self.title: str = title
    self.download_link: dict = download_link
    self.quality: str = quality
    self.webs_data: str = webs_data
    self.sts = sts


@Bot.on_callback_query(filters.regex("^close$"))
async def close_handler(_, query):
  """This Is Close Handler Of Callback Data"""
  await igrone_error(query.answer)()
  await retry_on_flood(query.message.delete)()


@Bot.on_callback_query(filters.regex("^search_") & is_auth_query())
async def episode_info_handler(_, query):
  """This Is Episode Info Handler Of Callback Data"""
  rdata = query.data.removeprefix("search_")
  
  if rdata in search_cache.get(query.from_user.id, {}):
    animeclass, back_data = search_cache.get(query.from_user.id, {}).pop(rdata)
    webs = await igrone_error(get_webs)(animeclass.web_data)
    if not webs:
       return await retry_on_flood(query.answer)("📐 ᴡᴇʙsɪᴛᴇ ɴᴏᴛ ғᴏᴜɴᴅ 📐", show_alert=True)
    
    animeclass = await webs.get_info(animeclass)
    await igrone_error(query.answer)()

    back_cache[f"{webs.sf}_{rdata}"] = back_data # donot change this
    episode_cache[rdata] = (animeclass, f"{webs.sf}_{rdata}")
    
    try:
      await retry_on_flood(query.edit_message_text)(
        text=animeclass.msg[:4096],
        reply_markup=InlineKeyboardMarkup([
          [
            InlineKeyboardButton(" 𝗘𝗽𝗶𝘀𝗼𝗱𝗲 ", callback_data=f"et{rdata}"),
            InlineKeyboardButton(" 𝐂𝐥𝐨𝐬𝐞 ", callback_data="qclose")
          ],
          [
            InlineKeyboardButton(" 𝗕𝗮𝗰𝗸 ", callback_data=f"ebk_{webs.sf}_{rdata}")
          ]]))
    except Exception:
      pass
  else:
    await retry_on_flood(query.answer)(" This is an old button, please redo the search ", show_alert=True)


async def get_episode_button(animeclass, webs, back_data, rdata, page: int = 1):
  button = []

  start_len = episode_len * (page - 1)
  end_len = episode_len * page + 1  # +1 to check next page exists

  count = 0
  next_exists = None
  async for data in islice(webs.get_episodes(animeclass, page=page), start_len, end_len):
    if count < episode_len:
          episode_cache[data.unique()] = (data, webs)
          button.append(InlineKeyboardButton(data.title, callback_data=f"wt{data.unique()}"))
          count += 1
    else:
      next_exists = True
      break
  
  if count == 0:
    return None

  button = split_list(button)

  arrow_c = str(hash(f"{animeclass.unique()}{webs.sf}"))
  episode_cache[arrow_c] = (animeclass, back_data)

  arrow = []
  if page > 1:
      arrow.append(InlineKeyboardButton("<<", callback_data=f"et{rdata}_{page-1}"))
  if next_exists:
      arrow.append(InlineKeyboardButton(">>", callback_data=f"et{rdata}_{page+1}"))

  if arrow:
      button.append(arrow)
  
  button.append([
    InlineKeyboardButton(" 𝗙𝘂𝗹𝗹 𝗣𝗮𝗴𝗲 ", callback_data=f"all{rdata}_{page}")
  ])
  
  button.append([
    InlineKeyboardButton(" 𝗕𝗮𝗰𝗸 ", callback_data=f"ebk_{back_data}"),
    InlineKeyboardButton(" 𝐂𝐥𝐨𝐬𝐞 ", callback_data="qclose")
  ])
  
  return button
  


@Bot.on_callback_query(filters.regex("^et")) # eps_rdata_page
async def episode_loader_handler(_, query):
  """This Is Episode Loader Handler Of Callback Data"""
  rdata = query.data.removeprefix("et")
  rdata = rdata
  page = 1
  if "_" in rdata:
    rdata_list = rdata.split("_")
    rdata = rdata_list[0]
    page = int(rdata_list[1])
  
  animeclass, back_data = episode_cache.get(rdata, (None, None))
  webs = await igrone_error(get_webs)(animeclass.web_data) if animeclass else None
  
  if not animeclass or not webs:
     return await retry_on_flood(query.answer)(" This is an old button, please redo the search ", show_alert=True)
  
  if button := await get_episode_button(animeclass, webs, back_data, rdata, page):
    await igrone_error(query.answer)()
    await retry_on_flood(query.edit_message_reply_markup)(InlineKeyboardMarkup(button))
  else:
    await igrone_error(query.answer)(" No episodes found ", show_alert=True)

@Bot.on_callback_query(filters.regex("^wt") & is_auth_query())
async def episode_download_handler(_, query):
    rdata = query.data.removeprefix("wt")
    episodeclass, webs = episode_cache.get(rdata, (None, None))
    if not episodeclass or not webs:
        return await retry_on_flood(query.answer)(" This is an old button, please redo the search ", show_alert=True)
    
    if webs.sf == "AA":  # AllAnime
        buttons = []
        if episodeclass.data.get("sub_url"):
            buttons.append([InlineKeyboardButton("SUB (1080p)", callback_data=f"sub_{rdata}")])
        if episodeclass.data.get("dub_url"):
            buttons.append([InlineKeyboardButton("DUB (1080p)", callback_data=f"dub_{rdata}")])
        buttons.append([InlineKeyboardButton(" 𝐂𝐥𝐨𝐬𝐞 ", callback_data="close")])
        await igrone_error(query.answer)()
        await retry_on_flood(query.message.reply_text)(
            f"<blockquote><b>📥 Choose version for {episodeclass.title} - {episodeclass.anime_title} 📥</b></blockquote>",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    else:
      await webs.get_downloading_links(episodeclass)
      if not episodeclass.download_links:
        return await retry_on_flood(query.answer)(" No download links found ", show_alert=True)
        
      button = []

      if webs.sf == "AZ":
        button = [
          InlineKeyboardButton(episode['quality'], callback_data=f"dl{rdata}_{i}")
          for i, episode in enumerate(episodeclass.download_links)
        ]
        button = split_list(button)
      else:
        button = [
          [InlineKeyboardButton(episode['quality'], callback_data=f"dl{rdata}_{i}")]
          for i, episode in enumerate(episodeclass.download_links)
        ]
      
      button.append([InlineKeyboardButton(" 𝐂𝐥𝐨𝐬𝐞 ", callback_data="close")])
      await igrone_error(query.answer)()
      await retry_on_flood(query.message.reply_text)(
            f"<blockquote><b>📥 Choose Quality of {episodeclass.title} - {episodeclass.anime_title} 📥</b></blockquote>",
            reply_markup=InlineKeyboardMarkup(button)
      )

@Bot.on_callback_query(filters.regex("^(sub|dub)_"))
async def allanime_version_handler(_, query):
    ep_type, rdata = query.data.split("_", 1)
    episodeclass, webs = episode_cache.get(rdata, (None, None))
    if not episodeclass or not webs or webs.sf != "AA":
        return await retry_on_flood(query.answer)(" This is an old button, please redo the search ", show_alert=True)

    ep_url = episodeclass.data.get(f"{ep_type}_url", "")
    episodeclass.download_links = [{"quality": "1080p", "link": ep_url}] if ep_url else []
    if not episodeclass.download_links:
        return await retry_on_flood(query.answer)("No download link found for this version.", show_alert=True)

    if Queue.is_user_hit_limit(query.from_user.id):
        return await retry_on_flood(query.answer)(
            f"You have reached the maximum limit of {Queue.user_limit} tasks", show_alert=True)

    sts = await retry_on_flood(query.message.reply_text)(
        "<code>Adding...</code>"
    )

    downloading_ = Downloading_(
        download_link=episodeclass.download_links[0],
        anime_title=episodeclass.anime_title,
        title=episodeclass.title,
        quality=episodeclass.download_links[0]["quality"],
        webs_data=webs.sf,
        sts=sts,
    )
    task_id, queue_number = await Queue.put(downloading_, user_id=query.from_user.id)
    await igrone_error(add_user)(query.from_user.id)
    await igrone_error(query.answer)()
    await retry_on_flood(sts.edit_text)(
        f"<blockquote><b>📥 Downloading {episodeclass.title} {ep_type.upper()} - {episodeclass.anime_title} 📥</b></blockquote>\n\n<b>📌 Task ID:</b> <code>{task_id}</code>\n<b>📌 Task Number:</b> <code>{queue_number}</code>",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📌 𝐂𝐚𝐧𝐜𝐞𝐥 𝐓𝐚𝐬𝐤 📌", callback_data=f"cancel_{task_id}")
            ]
        ])
    )

@Bot.on_callback_query(filters.regex("^dl"))
async def dl_callback_handler(episodeclass, query):
  """ This Is Add To Queue Handler Of Callback Data """
  rdata = query.data.removeprefix("dl")
  try:
    rdata, list_index = rdata.split("_")
  except:
    return await igrone_error(query.answer)(" This is an old button, please redo the search ", show_alert=True)

  episodeclass, webs = episode_cache.get(rdata, (None, None))
  if not episodeclass or not webs:
     return await retry_on_flood(query.answer)(" This is an old button, please redo the search ", show_alert=True)

  if not episodeclass.download_links:
     return await retry_on_flood(query.answer)(" No download links found ", show_alert=True)

  if Queue.is_user_hit_limit(query.from_user.id):
     return await retry_on_flood(query.answer)(f" You have reached the maximum limit of {Queue.user_limit} tasks ", show_alert=True)
  
  sts = await retry_on_flood(query.message.reply_text)("<code>Adding...</code>")

  downloading_ = Downloading_(
    download_link=episodeclass.download_links[int(list_index)],  
    anime_title=episodeclass.anime_title, 
    title=episodeclass.title,
    quality=episodeclass.download_links[int(list_index)]['quality'],
    webs_data=webs.sf,
    sts=sts,
  )
  
  task_id, queue_number = await Queue.put(downloading_, user_id=query.from_user.id)
  await igrone_error(add_user)(query.from_user.id)
  await igrone_error(query.answer)()
  await retry_on_flood(sts.edit_text)(
      f"<blockquote><b>📥 Added AT Queue {episodeclass.title} - {episodeclass.anime_title} 📥</b></blockquote>\n\n<b>📌 Task ID:</b> <code>{task_id}</code>\n<b>📌 Task Number:</b> <code>{queue_number}</code>",
      reply_markup=InlineKeyboardMarkup([
        [
          InlineKeyboardButton("📌 𝐂𝐚𝐧𝐜𝐞𝐥 𝐓𝐚𝐬𝐤 📌", callback_data=f"cancel_{task_id}")
        ]
      ])
  )

# -------- Batch Download Handler -------
@Bot.on_callback_query(filters.regex("^all") & is_auth_query())
async def all_episode_download_handler(_, query):
  rdata = query.data.removeprefix("all")
  rdata = rdata.split("_")[0]
  page = int(query.data.split("_")[1]) if "_" in query.data else 1

  animeclass, back_data = episode_cache.get(rdata, (None, None))
  webs = await igrone_error(get_webs)(animeclass.web_data) if animeclass else None
  if not animeclass or not webs:
      return await retry_on_flood(query.answer)(" This is an old button, please redo the search ", show_alert=True)

  if webs.sf == "AA":
    start_len = episode_len * (page - 1)
    end_len = episode_len * page
    eps = [ep async for ep in islice(webs.get_episodes(animeclass, page=page), start_len, end_len)]
    any_sub = any(ep.data.get("sub_url") for ep in eps)
    any_dub = any(ep.data.get("dub_url") for ep in eps)
    buttons = []
    if any_sub:
      buttons.append([InlineKeyboardButton("Download All SUB (1080p)", callback_data=f"aabatch_{rdata}_{page}_sub")])
    if any_dub:
      buttons.append([InlineKeyboardButton("Download All DUB (1080p)", callback_data=f"aabatch_{rdata}_{page}_dub")])
    buttons.append([InlineKeyboardButton(" 𝐂𝐥𝐨𝐬𝐞 ", callback_data="close")])
    await igrone_error(query.answer)()
    await retry_on_flood(query.message.reply_text)(
            f"<b>📥 Choose which version to download for all episodes on this page:</b>",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    return
  elif webs.sf == "AP":
    reply_markup = InlineKeyboardMarkup([
      [
        InlineKeyboardButton(" 𝟑𝟔𝟎𝐩 (𝐒𝐮𝐛) ", callback_data=f"qa{rdata}_{page}_4_s"),
        InlineKeyboardButton(" 𝟕𝟒𝟎𝐩 (𝐒𝐮𝐛) ", callback_data=f"qa{rdata}_{page}_7_s")
      ], 
      [
        InlineKeyboardButton(" 𝟏𝟎𝟖𝟎𝐩 (𝐒𝐮𝐛) ", callback_data=f"qa{rdata}_{page}_1_s"),
      ],
      [
        InlineKeyboardButton(" -------------------------------------------------------------------------------------------- ", copy_text=" 𝗞𝗼𝗻𝗻𝗶𝗰𝗵𝗶𝘄𝗮 𝗦𝗲𝗻𝗽𝗮𝗶 , 𝗴𝗼-𝗿𝗶𝘆ō 𝗮𝗿𝗶𝗴𝗮𝘁ō 𝗴𝗼𝘇𝗮𝗶𝗺𝗮𝘀𝘂.. "),
      ],
      [
        InlineKeyboardButton(" 𝟑𝟔𝟎𝐩 (𝐃𝐮𝐛) ", callback_data=f"qa{rdata}_{page}_4_d"),
        InlineKeyboardButton(" 𝟕𝟒𝟎𝐩 (𝐃𝐮𝐛) ", callback_data=f"qa{rdata}_{page}_7_d")
      ], 
      [
        InlineKeyboardButton(" 𝟏𝟎𝟖𝟎𝐩 (𝐃𝐮𝐛) ", callback_data=f"qa{rdata}_{page}_1_d"),
      ],
      [
        InlineKeyboardButton(" 𝐂𝐥𝐨𝐬𝐞 ", callback_data="close")
      ]
    ])
  elif webs.sf == "AX":
    reply_markup = InlineKeyboardMarkup([
      [
        InlineKeyboardButton(" 𝟑𝟔𝟎𝐩 (𝐒𝟏) ", callback_data=f"qa{rdata}_{page}_4_1"),
        InlineKeyboardButton(" 𝟕𝟒𝟎𝐩 (𝐒𝟏) ", callback_data=f"qa{rdata}_{page}_7_1"),
      ],
      [
        InlineKeyboardButton(" 𝟏𝟎𝟖𝟎𝐩 (𝐒𝟏) ", callback_data=f"qa{rdata}_{page}_1_1"),
        InlineKeyboardButton(" 𝟒𝐊 (𝐒𝟏) ", callback_data=f"qa{rdata}_{page}_a_1")
      ],
      [
        InlineKeyboardButton(" -------------------------------------------------------------------------------------------- ", copy_text=" 𝗞𝗼𝗻𝗻𝗶𝗰𝗵𝗶𝘄𝗮 𝗦𝗲𝗻𝗽𝗮𝗶 , 𝗴𝗼-𝗿𝗶𝘆ō 𝗮𝗿𝗶𝗴𝗮𝘁ō 𝗴𝗼𝘇𝗮𝗶𝗺𝗮𝘀𝘂.. "),
      ],
      [
        InlineKeyboardButton(" 𝟑𝟔𝟎𝐩 (𝐒𝟐) ", callback_data=f"qa{rdata}_{page}_4_2"),
        InlineKeyboardButton(" 𝟕𝟒𝟎𝐩 (𝐒𝟐) ", callback_data=f"qa{rdata}_{page}_7_2"),
      ],
      [
        InlineKeyboardButton(" 𝟏𝟎𝟖𝟎𝐩 (𝐒𝟐) ", callback_data=f"qa{rdata}_{page}_1_2"),
        InlineKeyboardButton(" 𝟒𝐊 (𝐒𝟐) ", callback_data=f"qa{rdata}_{page}_a_2")
      ],
      [
        InlineKeyboardButton(" 𝐂𝐥𝐨𝐬𝐞 ", callback_data="close")
      ]
    ])
  else:
    return await igrone_error(query.answer)(" That is not supported yet ")
  
  await igrone_error(query.answer)()
  await retry_on_flood(query.message.reply_text)(
      f"<blockquote><b>📥 Choose Quality of {animeclass.title} from Page: {page} 📥</b></blockquote>",
      reply_markup=reply_markup
  )

@Bot.on_callback_query(filters.regex("^aabatch_"))
async def allanime_batch_download_handler(_, query):
    # Syntax: aabatch_{rdata}_{page}_{version}
    _, rdata, page, version = query.data.split("_", 3)
    page = int(page)
    animeclass, back_data = episode_cache.get(rdata, (None, None))
    webs = await igrone_error(get_webs)(animeclass.web_data) if animeclass else None
    if not animeclass or not webs or webs.sf != "AA":
        return await retry_on_flood(query.answer)(" This is an old button, please redo the search ", show_alert=True)

    if Queue.is_user_hit_limit(query.from_user.id):
        return await retry_on_flood(query.answer)(
            f"You have reached the maximum limit of {Queue.user_limit} tasks", show_alert=True)

    # Gather episodes for the chosen page
    start_len = episode_len * (page - 1)
    end_len = episode_len * page
    eps = [ep async for ep in islice(webs.get_episodes(animeclass, page=page), start_len, end_len)]

    to_queue = []
    for ep in eps:
        ep_url = ep.data.get(f"{version}_url", None)
        if ep_url:
            ep.download_links = [{"quality": "1080p", "link": ep_url}]
            downloading_ = Downloading_(
                download_link=ep.download_links[0],
                anime_title=ep.anime_title,
                title=ep.title + f" ({version.upper()})",
                quality="1080p",
                webs_data=webs.sf
            )
            to_queue.append(downloading_)

    if not to_queue:
        return await retry_on_flood(query.answer)("No episodes found for that version.", show_alert=True)
    added = 0
    user_id = query.from_user.id
    for d in to_queue:
        if not Queue.is_user_hit_limit(user_id):
            await Queue.put(d, user_id=user_id)
            added += 1
        else:
            break

    await igrone_error(add_user)(user_id)
    return await retry_on_flood(query.answer)(
        f"Added {added} episodes ({version.upper()}) to queue!"
    )

@Bot.on_callback_query(filters.regex("^qa"))
async def all_episode_download_handler(_, query):
    """This Is All Episode Download Handler Of Callback Data"""
    rdata = query.data.removeprefix("qa")
    rdata, page, r_quality, server = rdata.split("_")
    quality_map = {"4": "360", "7": "720", "8": "1080"}
    r_quality = quality_map.get(r_quality, r_quality)
    page = int(page)

    animeclass, back_data = episode_cache.get(rdata, (None, None))
    webs = await igrone_error(get_webs)(animeclass.web_data) if animeclass else None
    if not animeclass or not webs:
        return await retry_on_flood(query.answer)("This is an old button, please redo the search", show_alert=True)
    
    if Queue.is_user_hit_limit(query.from_user.id):
        return await retry_on_flood(query.answer)(f"You have reached the maximum limit of {Queue.user_limit} tasks", show_alert=True)

    logger.debug(f"Processing page {page} with quality {r_quality} and server {server}")
    start_len = episode_len * (page - 1)
    end_len = episode_len * page

    episodes_to_process = [
        episodeclass
        async for episodeclass in islice(webs.get_episodes(animeclass, page=page), start_len, end_len)
    ]

    download_tasks = [
        webs.get_downloading_links(episodeclass) 
        for episodeclass in episodes_to_process
    ]
    download_results = await asyncio.gather(*download_tasks)

    episodes_with_links = reversed(list(zip(episodes_to_process, download_results)))

    def check_quality(episodeclass):
        """This will give particular quality link from particular episodeclass"""
        if not episodeclass.download_links:
            return (None, None)
        
        checker_ = (None, None)
        if webs.sf == "AP":
          checker_ = next(
            (
              (quality_data, c_quality)
              for quality_data in episodeclass.download_links
              if (quality := quality_data['quality'])
              if (c_quality := get_quality_num(quality, type=r_quality)) and ((server == "d" and "eng" in quality) or (server == "s" and "eng" not in quality))
            ),
            (None, None)
          )
        elif webs.sf == "AX":
          checker_ = next(
            (
              (quality_data, None) if r_quality == "a" else (quality_data, r_quality)
              for quality_data in episodeclass.download_links
              if (quality := quality_data.get('quality', None))
              if f"Server {server}" in quality
            ),
            (None, None)
          )
        return checker_

    queue_operations = []
    user_id = query.from_user.id

    queue_operations = [
      Queue.put(
          Downloading_(
              download_link=quality_data[0],  
              anime_title=episodeclass.anime_title, 
              title=episodeclass.title,
              quality=quality_data[1],
              webs_data=webs.sf,
          ),
          user_id=user_id
      )
      for episodeclass, download_links in episodes_with_links
      if Queue.is_user_hit_limit(user_id) is False and (quality_data := check_quality(episodeclass))
    ]
    if queue_operations:
      await retry_on_flood(query.answer)(f"Added {len(queue_operations)} tasks to queue successfully! and Some were removed due to user limit.. ")
      await asyncio.gather(*queue_operations)
      await igrone_error(add_user)(user_id)
    else:
      await retry_on_flood(query.answer)("No tasks were added to queue.", show_alert=True)



# ----- ca
