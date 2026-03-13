from bot import Bot, Vars
from .storage import *
import random
from pyrogram.types import InputMediaPhoto

@Bot.on_callback_query(dynamic_data_filter("refresh"))
async def refresh_handler(_, query):
  if not _.FSB or _.FSB == []:
    await retry_on_flood(query.answer)(
      " ✅ Thanks for joining! You can now use the bot. ",
    )
    
    return await retry_on_flood(query.message.delete)()

  channel_button, change_data = await check_fsb(_, query)
  if not channel_button:
    await retry_on_flood(query.answer)(
      " ✅ Thanks for joining! You can now use the bot. "
    )
    return await retry_on_flood(query.message.delete)()

  channel_button = split_list(channel_button)
  channel_button.append([InlineKeyboardButton("🔃 Refresh 🔃", callback_data="refresh")])

  try:
    await retry_on_flood(query.edit_message_media)(
        media=InputMediaPhoto(random.choice(Vars.PICS),
                              caption=Vars.FORCE_SUB_TEXT),
        reply_markup=InlineKeyboardMarkup(channel_button),
    )
  except:
    await retry_on_flood(query.answer)("You're still not in the channel.")

  if change_data:
    for change_ in change_data:
      _.FSB[change_[0]] = (change_[1], change_[2], change_[3])


@Bot.on_message(filters.command(["clean_tasks", "clean_queue"]))
async def deltask(client, message):
  if Vars.IS_PRIVATE:
    if message.chat.id not in Vars.ADMINS:
      return await message.reply("<code>You cannot use me baby </code>")

  try:
    if Queue.get_count(message.from_user.id) != 0:
      numb = await Queue.delete_tasks(message.from_user.id)
      await retry_on_flood(message.reply)(f"<i>All Your Tasks Deleted:- {numb} </i>")
    else:
      await retry_on_flood(message.reply)("<i>There is no any your pending tasks.... </i>")
  except Exception as err:
    await retry_on_flood(message.reply)(f"<code>Error Occured: {err}</code>")


@Bot.on_callback_query(filters.regex("^clean_queue$"))
async def clean_queue_handler(_, query):
  try:
    if Queue.get_count(query.from_user.id) != 0:
      numb = await Queue.delete_tasks(query.from_user.id)
      await query.answer(f" All Your Tasks Deleted:- {numb}  ")
    else:
      await query.answer(" There is no any your pending tasks.... ")
  except Exception:
    await query.answer(" Error Occured ")



@Bot.on_message(filters.command("queue"))
async def queue_msg_handler(_, message):
  if Vars.IS_PRIVATE:
    if message.chat.id not in Vars.ADMINS:
      return await message.reply("<code>You cannot use me baby </code>")

  sts = await retry_on_flood(message.reply)(
    "<code>Processing...</code>", 
    quote=True,
    reply_markup=InlineKeyboardMarkup([
      [
        InlineKeyboardButton("⌜ 𝙲𝚕𝚎𝚊𝚗 𝚀𝚞𝚎𝚞𝚎 ⌟", callback_data="clean_queue"),
      ],
      [
        InlineKeyboardButton(" 𝕽𝖊𝖋𝖗𝖊𝖘𝖍 ", callback_data="refresh_queue"),
        InlineKeyboardButton(" ▏𝗖𝗟𝗢𝗦𝗘▕ ", callback_data="qclose")
      ]
    ])
  )
  queue_text = await get_queue_text(_, message)
  await retry_on_flood(sts.edit_media)(
    InputMediaPhoto(random.choice(Vars.PICS), caption=queue_text),
    reply_markup=InlineKeyboardMarkup([
      [
        InlineKeyboardButton("⌜ 𝙲𝚕𝚎𝚊𝚗 𝚀𝚞𝚎𝚞𝚎 ⌟", callback_data="clean_queue"),
      ],
      [
        InlineKeyboardButton(" 𝕽𝖊𝖋𝖗𝖊𝖘𝖍 ", callback_data="refresh_queue"),
        InlineKeyboardButton(" ▏𝗖𝗟𝗢𝗦𝗘▕ ", callback_data="qclose")
      ]
    ])
    )

@Bot.on_callback_query(filters.regex("^refresh_queue$"))
async def refresh_queue_handler(_, query):
  queue_text = await get_queue_text(_, query)
  try:
    await retry_on_flood(query.edit_message_media)(
      InputMediaPhoto(random.choice(Vars.PICS), caption=queue_text),
      reply_markup=InlineKeyboardMarkup([
        [
          InlineKeyboardButton("⌜ 𝙲𝚕𝚎𝚊𝚗 𝚀𝚞𝚎𝚞𝚎 ⌟", callback_data="clean_queue"),
        ],
        [
          InlineKeyboardButton(" 𝕽𝖊𝖋𝖗𝖊𝖘𝖍 ", callback_data="refresh_queue"),
          InlineKeyboardButton(" ▏𝗖𝗟𝗢𝗦𝗘▕ ", callback_data="qclose")
        ]
      ]))
  except Exception:
    await igrone_error(query.answer)(" Doned ")


async def get_queue_text(client, message):
  queue_text = f"<blockquote>**📌 Queue Status (Total: {Queue.qsize()} Episode)**</blockquote>\n"
  queue_text += "\n**👤 Your queue:-**\n"
  
  if (count := Queue.get_count(message.from_user.id)) != 0:
    qdata = Queue.get_available_tasks(message.from_user.id)
    if isinstance(qdata, list):
      qdata = qdata[0]
    if qdata is None:
      queue_text += "__=> No chapters in your queue.__\n"
    else:
      queue_text += "<blockquote>"
      queue_text += f"__=> Total Tasks:- {count}__\n"
      queue_text += f"__=> {qdata.data.title} - {qdata.data.anime_title}__</blockquote>\n"
  else:
    queue_text += "__=> No chapters in your queue.__\n"
  
  queue_text += "\n🚦 Now Processing:\n"
  if Queue.ongoing_tasks:
    queue_text += "<blockquote expandable>"
    for qdata in Queue.ongoing_tasks.values():
      user_ = await client.get_users(int(qdata.user_id))
      queue_text += f"=> {user_.mention()}\n"
    queue_text += "</blockquote>\n"
  else:
    queue_text += "__=> No chapters are being processed.__\n\n"
  
  queue_text += "__=> Other chapters are in the waiting line.__"
  
  return queue_text

