from asyncio import timeout
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from pyrogram.errors import FloodWait
from .storage import retry_on_flood, igrone_error
from bot import Bot, Vars, logger
from Tools.db import uts, update_setting, ensure_user
import random

users_txt = """<b>Welcome to the User Panel ! </b>

<b>=> Your User ID: <code>{id}</code></b>
<b>=> File Name: <code>{file_name}</code><code>[{len}]</code></b>
<b>=> Caption: <code>{caption}</code></b>
<b>=> Thumbnail: <code>{thumb}</code></b>
<b>=> Output Mode: <code>{type}</code></b>
<b>=> Dump Channel: <code>{dump}</code></b>"""


async def get_user_txt(user_id):
  user_id = str(user_id)
  await ensure_user(user_id)
  
  thumbnali = uts[user_id]['setting'].get("thumb", None)
  mode = uts[user_id]['setting'].get("mode", None)
  mode = "Video" if not mode else "Document"
  txt = users_txt.format(
    id=user_id,
    file_name=uts[user_id]['setting'].get("file_name", "None"),
    caption=uts[user_id]['setting'].get("caption", "None"),
    thumb="True" if thumbnali else "None",
    dump=uts[user_id]['setting'].get("dump", "None"),
    type=mode,
    megre=uts[user_id]['setting'].get("megre", "None"),
    regex=uts[user_id]['setting'].get("regex", "None"),
    len=uts[user_id]['setting'].get("f_n_l", "None"),
  )
  return txt, thumbnali


@Bot.on_message(filters.command("info") & filters.user(Vars.ADMINS))
async def info_handler(_, message):
  if message.reply_to_message:
    user_id = message.reply_to_message.from_user.id
  else:
    try: user_id = str(message.text.split(" ")[1])
    except: return await retry_on_flood(message.reply_text)("<code>Please reply to a message or provide a user id</code>")
  
  sts = await retry_on_flood(message.reply)("<code>Processing...</code>", quote=True)
  await ensure_user(user_id)
  txt, thumbnali = await get_user_txt(user_id)
  
  if not thumbnali:
    thumbnali = random.choice(Vars.PICS)
  try:
    await retry_on_flood(sts.edit_media)(
      InputMediaPhoto(thumbnali, caption=txt),
      reply_markup=InlineKeyboardMarkup([
        [
          InlineKeyboardButton(" ▏𝗖𝗟𝗢𝗦𝗘▕ ", callback_data="qclose")
        ]
      ])
    )
  except:
    await retry_on_flood(sts.edit_media)(
      InputMediaPhoto(Vars.PICS[-2], caption=txt),
      reply_markup=InlineKeyboardMarkup([
        [
          InlineKeyboardButton(" ▏𝗖𝗟𝗢𝗦𝗘▕ ", callback_data="qclose")
        ]
      ])
    )


@Bot.on_message(filters.command(["us", "user_setting", "user_panel"]))
async def userxsettings(client, message):
  if Vars.IS_PRIVATE:
    if message.chat.id not in Vars.ADMINS:
      return await message.reply("<code>You cannot use me baby </code>")

  sts = await message.reply("<code>Processing...</code>")
  try:
    txt, thumbnali = await get_user_txt(message.from_user.id)

    button = [
      [
        InlineKeyboardButton("⌜ғɪʟᴇ ɴᴀᴍᴇ⌟", callback_data="show_file_name"),
        InlineKeyboardButton("⌜ᴄᴀᴘᴛɪᴏɴ⌟", callback_data="show_caption")
      ],
      [
        InlineKeyboardButton("⌜ᴛʜᴜᴍʙɴᴀɪʟ⌟", callback_data="show_thumb"),
        InlineKeyboardButton("⌜ʀᴇɢᴇx⌟", callback_data="show_regex")
      ],
      [
        InlineKeyboardButton("⌜ғɪʟᴇ ᴛʏᴘᴇ⌟", callback_data="show_type"),
        InlineKeyboardButton("⌜ᴅᴜᴍᴘ ᴄʜᴀɴɴᴇʟ⌟", callback_data="show_dump"),
      ],
      [
        InlineKeyboardButton("▏𝗖𝗟𝗢𝗦𝗘▕", callback_data="qclose")
      ]
    ]
    
    if not thumbnali:
      thumbnali = random.choice(Vars.PICS)
    try:
      await retry_on_flood(message.reply_photo)(
        thumbnali,
        caption=txt,
        reply_markup=InlineKeyboardMarkup(button),
        quote=True,
      )
    except:
      await retry_on_flood(message.reply_photo)(
        Vars.PICS[0],
        caption=txt,
        reply_markup=InlineKeyboardMarkup(button),
        quote=True
      )

    await sts.delete()
  except Exception as err:
    logger.exception(err)
    await sts.edit(err)




@Bot.on_callback_query(filters.regex("^main_settings$"))
async def main_settings_handler(client, query):
  try:
    txt, thumbnali = await get_user_txt(query.from_user.id)

    button = [
      [
        InlineKeyboardButton("⌜ғɪʟᴇ ɴᴀᴍᴇ⌟", callback_data="show_file_name"),
        InlineKeyboardButton("⌜ᴄᴀᴘᴛɪᴏɴ⌟", callback_data="show_caption")
      ],
      [
        InlineKeyboardButton("⌜ᴛʜᴜᴍʙɴᴀɪʟ⌟", callback_data="show_thumb"),
        InlineKeyboardButton("⌜ʀᴇɢᴇx⌟", callback_data="show_regex")
      ],
      [
        InlineKeyboardButton("⌜ғɪʟᴇ ᴛʏᴘᴇ⌟", callback_data="rts_type"),
        InlineKeyboardButton("⌜ᴅᴜᴍᴘ ᴄʜᴀɴɴᴇʟ⌟", callback_data="show_dump"),
      ],
      [
        InlineKeyboardButton("▏𝗖𝗟𝗢𝗦𝗘▕", callback_data="qclose")
      ]
    ]
    if not thumbnali:
      thumbnali = random.choice(Vars.PICS)
    
    try:
      await retry_on_flood(query.edit_message_media)(
        InputMediaPhoto(thumbnali, caption=txt),
        reply_markup=InlineKeyboardMarkup(button)
      )
    except:
      await retry_on_flood(query.edit_message_media)(
        InputMediaPhoto(Vars.PICS[-1], caption=txt),
        reply_markup=InlineKeyboardMarkup(button)
      )

  except Exception as err:
    logger.exception(err)
    await igrone_error(query.message.reply_text)(
      f"```{err}```"
    )


@Bot.on_callback_query(filters.regex("^show_"))
async def  show_settings_handler(_, query):
  type_data =  query.data.removeprefix("show_")
  #txt, thumbnail = get_user_txt(query.from_user.id)
  button = [
    [
      InlineKeyboardButton("⌜sᴇᴛ/ᴄʜᴀɴɢᴇ⌟", callback_data=f"ufn_{type_data}"),
      InlineKeyboardButton("▏ᴅᴇʟᴇᴛᴇ▕", callback_data=f"del_{type_data}")
    ]
  ]
  if type_data == "file_name":
    button.append([
      InlineKeyboardButton("⌜sᴇᴛ/ᴄʜᴀɴɢᴇ ʟᴇɴ⌟", callback_data="ufn_f_n_l"),
      InlineKeyboardButton("▏ᴅᴇʟᴇᴛᴇ ʟᴇɴ▕", callback_data="del_f_n_l")
    ])
  
  button.append([InlineKeyboardButton("⇦ 𝗕𝗔𝗖𝗞", callback_data="main_settings")])
  await retry_on_flood(query.edit_message_reply_markup)(InlineKeyboardMarkup(button))
  


@Bot.on_callback_query(filters.regex("^del_"))
async def del_settings_handler(_, query):
  type_data =  query.data.removeprefix("del_")
  
  user_id = str(query.from_user.id)
  reply_markup = query.message.reply_markup
  await ensure_user(user_id)
  
  if uts[user_id]['setting'].get(type_data, None):
    await update_setting(user_id, type_data, None)
    
    txt, thumbnail = await get_user_txt(query.from_user.id)
    await igrone_error(query.answer)(" Deleted Successfully ")
    if not thumbnail:
      thumbnail = random.choice(Vars.PICS)
    
    try:
      await retry_on_flood(query.edit_message_media)(
        InputMediaPhoto(thumbnail, caption=txt),
        reply_markup=reply_markup,
      )
    except:
      await retry_on_flood(query.edit_message_media)(
        InputMediaPhoto(Vars.PICS[-1], caption=txt),
        reply_markup=reply_markup,
      )
  else:
    await igrone_error(query.answer)(" Already Deleted ")



@Bot.on_callback_query(filters.regex("^ufn_"))
async def ufn_settings_handler(client, query):
  type_data =  query.data.removeprefix("ufn_")
  
  user_id = str(query.from_user.id)
  reply_markup = query.message.reply_markup

  caption = ""
  if type_data == "file_name":
    caption += "<b><code>{name}</code>: Anime Name\n<code>{ep}</code>: Anime Episode\n<code>{type}</code>: (SUB or DUB)\n<code>{res}</code>: Anime Resolution(480p, 720p, 1080p)\n\n/cancel : To Cancel Process</b>"
    caption += "\n\n<b><i>Example:-</i></b>\n<code>{name} - {ep} - {type} - {res}.mp4</code>"
  elif type_data == "caption":
    caption += "<b><code>{name}</code>: Anime Name\n<code>{ep}</code>: Anime Episode\n<code>{type}</code>: (SUB or DUB)\n<code>{res}</code>: Anime Resolution(480p, 720p, 1080p)\n<code>{}</code>: File Name\n\n/cancel : To Cancel Process</b>"
    caption += "\n\n<b><i>Note:- We will Accpet Html Format like Blod, Italic, etc </i></b>"
  elif type_data == "thumb":
    caption += "<b><i>Send Thumbnail Photo\n\n/cancel : To Cancel Process</i></b>"
  elif type_data == "dump":
    caption += "<b><i>Send Dump Channel ID or Foward Message from Channel \n\n/cancel : To Cancel Process</i></b>"
  elif type_data == "regex":
    caption += "<b><i>Send Regex(Zfill) Number like 1,2,3,etc</i></b>\n\n<code>This Will Add Zero Infornt of Number, If you set 1, then it will set 0 infornt of 1-9 to 01-09 , if you set 2 then it will set 0 infornt of 1-99 to 01-99 and viceversa </code>\n\n/cancel : To Cancel Process</i></b>"
  else:
    caption += "<b><i>Send File Name Length Number like 1,2,3,etc</i></b>\n\n<code>This Will Cut File Name Length, If you set 1, then it will cut file name length to 1, if you set 2 then it will cut file name length to 2 and viceversa</code> \n\n/cancel : To Cancel Process</i></b>"
  
  await igrone_error(query.answer)()
  await retry_on_flood(query.edit_message_media)(
    InputMediaPhoto(random.choice(Vars.PICS), caption=caption)
  )
  results_error = None
  try:
    call_ = await client.listen(
      user_id=int(user_id),
      timeout=80,
    )
    results_value = None
    if call_.text == "/cancel":
      results_error = "cancel"
      
    elif type_data in ["regex", "f_n_l"]:
      try: 
        results_value = int(call_.text)
      except:
        results_error = True
        
    elif type_data == "dump":
      if call_.text.startswith("-100"):
        try: 
           results_value = int(call_.text)
        except:
           results_error = True
        
      elif call_.forward_from_chat:
         results_value = call_.forward_from_chat.id or call_.forward_origin.chat.sender_chat
      else:
         results_error = True
      if results_value:
        try: 
          await client.get_chat(results_value)
        except:
          results_error = "cancel"
          await retry_on_flood(query.message.reply_text)(
            "<b><i>Please Add Bot For this Feature ......</i></b>"
          )
    
    elif type_data == "thumb":
      if call_.photo:
        results_value = call_.photo.file_id
      elif call_.document:
        results_value = call_.document.file_id
      else:
        results_error = True
    else:
      results_value = call_.text
    
    if results_error and results_error != "cancel":
      await retry_on_flood(query.message.reply_text)(
        "<b><i>Please Provide Correct Value ......</i></b>"
      )
    else:
      await update_setting(user_id, type_data, results_value)
      await igrone_error(call_.delete)()
  except Exception as err:
    logger.exception(err)
    await retry_on_flood(query.message.reply_text)(
      f"<b>Error Occured: {err}</b>"
    )
  finally:
    txt , thumbnail = await get_user_txt(query.from_user.id)
    if not thumbnail:
      thumbnail = random.choice(Vars.PICS)
    try:
      return await retry_on_flood(query.edit_message_media)(
         InputMediaPhoto(thumbnail, caption=txt),
         reply_markup=reply_markup,
      )
    except:
      return await retry_on_flood(query.edit_message_media)(
         InputMediaPhoto(Vars.PICS[-1], caption=txt),
         reply_markup=reply_markup,
      )
    



@Bot.on_callback_query(filters.regex("^rts_"))
async def rts_settings_handler(_, query):
  user_id = str(query.from_user.id)
  reply_markup = query.message.reply_markup
  await ensure_user(user_id)

  if query.data == "rts_video":
    await update_setting(user_id, "mode", None)
  elif query.data != "rts_type":
     await update_setting(user_id, "mode", "document")
  
  mode = uts[user_id]['setting'].get('mode', None)
  reply_markup = InlineKeyboardMarkup([
    [
      InlineKeyboardButton(f"{'✔' if not mode else '❌'} ️⌜ᴠɪᴅᴇᴏ⌟ {'✔' if not mode else '❌'}", callback_data="rts_video"),
      InlineKeyboardButton(f"{'✔' if mode else '❌'} ⌜ᴅᴏᴄᴜᴍᴇɴᴛ⌟ {'✔' if mode else '❌'}", callback_data="rts_document")
    ],
    [
      InlineKeyboardButton("⇦ 𝗕𝗔𝗖𝗞", callback_data="main_settings")
    ]
  ])
  await igrone_error(query.answer)()
  txt, thumbnail = await get_user_txt(query.from_user.id)
  if not thumbnail:
    thumbnail = random.choice(Vars.PICS)
  try:
    await retry_on_flood(query.edit_message_media)(
        InputMediaPhoto(thumbnail, caption=txt),
        reply_markup=reply_markup,
    )
  except:
    await retry_on_flood(query.edit_message_media)(
      InputMediaPhoto(Vars.PICS[1], caption=txt),
      reply_markup=reply_markup,
    )
