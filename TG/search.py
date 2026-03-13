from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto

from pyrogram.errors import FloodWait
from .storage import *

from Tools.db import add_user 
import asyncio

from bot import Bot, Vars
import random

logger = get_logger(__name__)

search_len = 15


@Bot.on_message(filters.text & filters.private & ~filters.regex(r"/"))
async def search(client, message):
  if Vars.IS_PRIVATE:
    if message.chat.id not in Vars.ADMINS:
      return await message.reply("<code>You cannot use me baby </code>")
  
  await add_user(message.from_user.id)
  photo = random.choice(Vars.PICS)

  try:
    await retry_on_flood(message.reply_photo)(
      photo, caption="<blockquote><i>Select search Webs ...</i></blockquote>",
      reply_markup=plugins_list(), quote=True
    )
  except ValueError:
    await retry_on_flood(message.reply_photo)(
      photo, caption="<blockquote><i>Select search Webs ...</i></blockquote>",
      reply_markup=plugins_list(), quote=True
    )


@Bot.on_message(filters.command("search"))
async def search_group(client, message):
  if Vars.IS_PRIVATE:
    if message.chat.id not in Vars.ADMINS:
      return await message.reply("<code>You cannot use me baby </code>")
  
  await add_user(message.from_user.id)
  try:
    txt = message.text.split(" ", 1)[1]
  except:
    return await message.reply("<code>Format:- /search Manga </code>")
  
  photo = random.choice(Vars.PICS)

  try:
    await retry_on_flood(message.reply_photo)(
      photo, caption="<blockquote><i>Select search Webs ...</i></blockquote>",
      reply_markup=plugins_list(), quote=True
    )
  except ValueError:
    await retry_on_flood(message.reply_photo)(
      photo, caption="<blockquote><i>Select search Webs ...</i></blockquote>",
      reply_markup=plugins_list(), quote=True
    )



async def search_all(search, sts, max_concurrent=2):
  semaphore = asyncio.Semaphore(max_concurrent)
  all_results = []
  found_list = []
  no_found_list = []
  completed = 0

  async def search_and_collect(web, web_name):
      nonlocal completed

      async with semaphore:
          try:
              result = await web.search(search)
              
              if result:
                  all_results.extend(result)
                  found_list.append(web_name)
              else:
                  no_found_list.append(web_name)

              completed += 1

              try:
                  await sts.edit_message_caption(
                      f"<i>Searching: <b>{search}</b> | "
                      f"Progress: <b>{completed}/{len(web_data)}</b> | "
                      f"Current: <b>{web_name}</b></i>"
                  )
              except:
                  pass

          except Exception:
              no_found_list.append(web_name)
              completed += 1

  tasks = [search_and_collect(web, name) for name, web in web_data.items() if name != "Hanime TV"]
  await asyncio.gather(*tasks)

  found_txt = ", ".join(found_list) if found_list else ""
  no_found_txt = ", ".join(no_found_list) if no_found_list else ""

  return all_results, found_txt, no_found_txt
  

async def get_button_(results_data, user_id, webs, page) -> list:
  button = []
  for results_ in iterate_list(results_data, search_len, page):
    search_cache.setdefault(user_id, {})[results_.unique()] = (results_, results_data)
    if webs == "all":
      web = await igrone_error(get_webs)(results_.web_data)
      
      button.append([InlineKeyboardButton(f"{results_.title} [{web.name}]", callback_data=f"search_{results_.unique()}")])
    else:
      button.append([InlineKeyboardButton(results_.title, callback_data=f"search_{results_.unique()}")])

  arrow = []
  arrow_c = f"{results_data[0].unique()}{results_data[-1].unique()}"
  search_cache.setdefault(user_id, {})[arrow_c] = (results_data, webs)
  
  if iterate_list(results_data, search_len, page=page-1):
    arrow.append(InlineKeyboardButton("<<", callback_data=f"mul{arrow_c}_{page-1}"))

  if iterate_list(results_data, search_len, page=page+1):
    arrow.append(InlineKeyboardButton(">>", callback_data=f"mul{arrow_c}_{page+1}"))

  if arrow:
    button.append(arrow)

  button.append([
      InlineKeyboardButton("▏𝗖𝗟𝗢𝗦𝗘▕", callback_data="qclose"),
      InlineKeyboardButton("⇦ 𝗕𝗔𝗖𝗞", callback_data="bk"),
  ])
  return button 


@Bot.on_callback_query(filters.regex("^plugin_") & is_auth_query())
async def plugin_handler(_, query):
  rand_pic = random.choice(Vars.PICS)
  await add_user(query.from_user.id)
  
  plugin_name = query.data.removeprefix("plugin_").split("_")
  try: page = int(plugin_name[-1])
  except: page = 1
  
  plugin_name = plugin_name[0]

  webs = await igrone_error(get_webs)(plugin_name) if plugin_name != "all" else "all"
  
  try: 
    search_query = query.message.reply_to_message.text
    if search_query.startswith("/search"):
      search_query = search_query.split(" ", 1)[1]
  except Exception:
    await retry_on_flood(query.answer)(" This is an old button, please redo the search ", show_alert=True)
    try: 
      return await retry_on_flood(query.message.delete)()
    except Exception: 
      return

  #if not isinstance(webs, str) and webs.sf == "HT" and query.from_user.id not in Vars.ADMINS:
    #return await retry_on_flood(query.answer)(" You cannot use this, need permission ", show_alert=True)
    
  results_data = None
  found_txt = None
  no_found_txt = None
  if webs == "all" and search_query is not None:
    results_data, found_txt, no_found_txt = await search_all(search_query, query)
  elif webs is not None and search_query is not None:
    await retry_on_flood(query.edit_message_media)(
      InputMediaPhoto(rand_pic, caption=f"<blockquote><i>Searching {search_query} on {webs.name}......</i></blockquote>")
    )
    
    results_data = await webs.search(search_query)

  
  if not results_data and webs:
    return await retry_on_flood(query.edit_message_media)(
      InputMediaPhoto(Vars.PICS[-1], caption=f"<i>No results found on {webs.name}. </i>\n\n<i>Try at Other Webs ...</i>"),
      reply_markup=plugins_list(),
    )
    
  elif not webs:
    return await retry_on_flood(query.answer)(" This is an old button, please redo the search ", show_alert=True)

  
  button = await get_button_(results_data, query.from_user.id, webs, page)
  if webs != "all":
    caption_text = f"<blockquote expandable><i>Search <b>{search_query}</b> from <b>{webs.name}</b></i></blockquote>"
  else:
    caption_text = f"<blockquote><i>Search <b>{search_query}</b> from <b>All</b></i></blockquote>"
    caption_text += f"\n\n<blockquote expandable><b>Found Sites:</b> <i>{found_txt}</i></blockquote>" if found_txt else ""
    caption_text += f"\n\n<blockquote expandable><b>Not Found Sites:</b> <i>{no_found_txt}</i></blockquote>" if no_found_txt else ""

  await igrone_error(query.answer)()
  try:
    await retry_on_flood(query.edit_message_media)(
      media=InputMediaPhoto(rand_pic,
                            caption=caption_text[:1024]),
      reply_markup=InlineKeyboardMarkup(button))
  except:
    await retry_on_flood(query.edit_message_media)(
      media=InputMediaPhoto(Vars.PICS[0], caption=caption_text[:1024]),
      reply_markup=InlineKeyboardMarkup(button))
  


@Bot.on_callback_query(filters.regex("^bk$") & is_auth_query())
async def back_webs_handler(_, query):
  await igrone_error(query.answer)()
  return await retry_on_flood(query.edit_message_media)(
    InputMediaPhoto(random.choice(Vars.PICS), caption="<blockquote><i>Select search Webs ...</i></blockquote>"),
    reply_markup=plugins_list(),
  )


@Bot. on_callback_query(filters.regex("^qclose$") & is_auth_query())
async def close_handler(_, query):
  await igrone_error(query.answer)()
  try: await query.message.reply_to_message.delete()
  except: pass
  
  try: await retry_on_flood(query.message.delete)()
  except: pass




@Bot.on_callback_query(filters.regex("^mul") & is_auth_query())
async def mul_handler(_, query):
  try:
    rand_pic = random.choice(Vars.PICS)
    query_text = query.message.text
    
    data, page = query.data.removeprefix("mul").split("_")
    page = int(page)
    results_data, webs = search_cache.get(query.from_user.id, {}).get(data, None)
    button = await get_button_(results_data, query.from_user.id, webs, page)
    await igrone_error(query.answer)()
    try:
      await retry_on_flood(query.edit_message_media)(
        media=InputMediaPhoto(rand_pic, caption=query_text),
        reply_markup=InlineKeyboardMarkup(button))
    except:
      await retry_on_flood(query.edit_message_media)(
        media=InputMediaPhoto(Vars.PICS[0], caption=query_text),
        reply_markup=InlineKeyboardMarkup(button))
  except Exception:
     #logger.exception(er)
     await retry_on_flood(query.answer)(" This is an old button, please redo the search ", show_alert=True)





# ------- Episdoe To Search Back ------- 
@Bot.on_callback_query(filters.regex("^ebk_") & is_auth_query())
async  def epk_back_handler(_, query):
  """This Is Back Button Handler Of Callback Data"""
  rdata = query.data.removeprefix("ebk_")
  webs = rdata.split("_")[0]
  if rdata in back_cache:
    results_data = back_cache.get(rdata)
    webs = await igrone_error(get_webs)(webs)
    button = await get_button_(results_data, query.from_user.id, webs, page=1)
    await igrone_error(query.answer)()

    rand_pic = random.choice(Vars.PICS)
    try:
      await retry_on_flood(query.edit_message_media)(
        media=InputMediaPhoto(rand_pic, caption=f"<blockquote><i>Search are from {webs.name}</i></blockquote>"),
        reply_markup=InlineKeyboardMarkup(button))
    except:
      await retry_on_flood(query.edit_message_media)(
        media=InputMediaPhoto(Vars.PICS[0], caption=f"<blockquote><i>Search are from {webs.name}</i></blockquote>"),
        reply_markup=InlineKeyboardMarkup(button))

  else:
    query.data =  f"plugin_{webs}"
    try:
      return await plugin_handler(_, query)
    except Exception as er:
      logger.exception(er)
      try: 
         await retry_on_flood(query.answer)(" This is an old button, please redo the search ", show_alert=True)
      except Exception:
        pass 
      await igrone_error(query.message.delete)()
    
