# Ultroid - UserBot
# Copyright (C) 2021 TeamUltroid
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ >
# PLease read the GNU Affero General Public License in
# <https://www.github.com/TeamUltroid/Ultroid/blob/main/LICENSE/>.

import re
import sys
from asyncio.exceptions import TimeoutError as AsyncTimeOut
from os import execl, remove
from random import choice

from pyUltroid.functions.gdrive import authorize, create_token_file
from pyUltroid.functions.tools import get_paste, telegraph_client
from pyUltroid.startup.loader import Loader
from telegraph import upload_file as upl
from telethon import events
from telethon.tl.types import MessageMediaWebPage
from telethon.utils import get_peer_id

try:
    from carbonnow import Carbon
except ImportError:
    Carbon = None
from . import *

# --------------------------------------------------------------------#
telegraph = telegraph_client()
# --------------------------------------------------------------------#


def text_to_url(event):
    """function to get media url (with|without) Webpage"""
    if isinstance(event.media, MessageMediaWebPage):
        webpage = event.media.webpage
        if webpage and webpage.type in ["photo"]:
            return webpage.display_url
    return event.text


# --------------------------------------------------------------------#


TOKEN_FILE = "resources/auths/auth_token.txt"


@callback(
    re.compile(
        "sndplug_(.*)",
    ),
    owner=True,
)
async def send(eve):
    name = (eve.data_match.group(1)).decode("UTF-8")
    thumb = "resources/extras/inline.jpg"
    await eve.answer("■ Sending ■")
    if name.startswith("def"):
        plug_name = name.replace("def_plugin_", "")
        plugin = f"plugins/{plug_name}.py"
        data = "back"
    elif name.startswith("add"):
        plug_name = name.replace("add_plugin_", "")
        plugin = f"addons/{plug_name}.py"
        data = "buck"
    else:
        plug_name = name.replace("vc_plugin_", "")
        plugin = f"vcbot/{plug_name}.py"
        data = "vc_helper"
    buttons = [
        [
            Button.inline(
                "« Pᴀsᴛᴇ »",
                data=f"pasta-{plugin}",
            )
        ],
        [
            Button.inline("« Bᴀᴄᴋ", data=data),
        ],
    ]
    await eve.edit(file=plugin, thumb=thumb, buttons=buttons)


heroku_api, app_name = Var.HEROKU_API, Var.HEROKU_APP_NAME


@callback("updatenow", owner=True)
async def update(eve):
    repo = Repo()
    ac_br = repo.active_branch
    ups_rem = repo.remote("upstream")
    if heroku_api:
        import heroku3

        try:
            heroku = heroku3.from_key(heroku_api)
            heroku_app = None
            heroku_applications = heroku.apps()
        except BaseException:
            return await eve.edit("`Wrong HEROKU_API.`")
        for app in heroku_applications:
            if app.name == app_name:
                heroku_app = app
        if not heroku_app:
            await eve.edit("`Wrong HEROKU_APP_NAME.`")
            repo.__del__()
            return
        await eve.edit(get_string("clst_1"))
        ups_rem.fetch(ac_br)
        repo.git.reset("--hard", "FETCH_HEAD")
        heroku_git_url = heroku_app.git_url.replace(
            "https://", "https://api:" + heroku_api + "@"
        )
        if "heroku" in repo.remotes:
            remote = repo.remote("heroku")
            remote.set_url(heroku_git_url)
        else:
            remote = repo.create_remote("heroku", heroku_git_url)
        try:
            remote.push(refspec=f"HEAD:refs/heads/{ac_br}", force=True)
        except GitCommandError as error:
            await eve.edit(f"`Here is the error log:\n{error}`")
            repo.__del__()
            return
        await eve.edit("`Successfully Updated!\nRestarting, please wait...`")
    else:
        await eve.edit(get_string("clst_1"))
        call_back()
        await bash("git pull && pip3 install -r requirements.txt")
        execl(sys.executable, sys.executable, "-m", "pyUltroid")


@callback("changes", owner=True)
async def changes(okk):
    await okk.answer(get_string("clst_3"))
    repo = Repo.init()
    ac_br = repo.active_branch
    button = (Button.inline("Update Now", data="updatenow"),)
    changelog, tl_chnglog = gen_chlog(repo, f"HEAD..upstream/{ac_br}")
    cli = "\n\nClick the below button to update!"
    if Carbon:
        try:
            await okk.edit("• Writing Changelogs 📝 •")
            carbon = Carbon(
                base_url="https://carbonara-42.herokuapp.com/api/cook",
                code=tl_chnglog,
                background=choice(ATRA_COL),
                language="md",
            )
            img = await carbon.memorize("changelog")
            return await okk.edit(
                f"**• Ultroid Userbot •**{cli}", file=img, buttons=button
            )
        except Exception as er:
            LOGS.exception(er)
    changelog_str = changelog + cli
    if len(changelog_str) > 1024:
        await okk.edit(get_string("upd_4"))
        await asyncio.sleep(2)
        with open("ultroid_updates.txt", "w+") as file:
            file.write(tl_chnglog)
        await okk.edit(
            get_string("upd_5"),
            file="ultroid_updates.txt",
            buttons=Button.inline("Update Now", data="updatenow"),
        )
        remove("ultroid_updates.txt")
        return
    await okk.edit(
        changelog_str,
        buttons=button,
        parse_mode="html",
    )


@callback(
    re.compile(
        "pasta-(.*)",
    ),
    owner=True,
)
async def _(e):
    ok = (e.data_match.group(1)).decode("UTF-8")
    with open(ok, "r") as hmm:
        _, key = await get_paste(hmm.read())
    link = "https://spaceb.in/" + key
    raw = f"https://spaceb.in/api/v1/documents/{key}/raw"
    if not _:
        return await e.answer(key[:30], alert=True)
    data = "back" if ok.startswith("plugins") else "buck"
    await e.edit(
        f"<strong>Pasted\n👉 <a href={link}>[Link]</a>\n👉 <a href={raw}>[Raw Link]</a></strong>",
        buttons=Button.inline("« Bᴀᴄᴋ", data=data),
        link_preview=False,
        parse_mode="html",
    )


@callback("authorise", owner=True)
async def _(e):
    if not e.is_private:
        return
    if not udB.get("GDRIVE_CLIENT_ID"):
        return await e.edit(
            "Client ID and Secret is Empty.\nFill it First.",
            buttons=Button.inline("Back", data="gdrive"),
        )
    storage = await create_token_file(TOKEN_FILE, e)
    authorize(TOKEN_FILE, storage)
    f = open(TOKEN_FILE)
    token_file_data = f.read()
    udB.set("GDRIVE_TOKEN", token_file_data)
    await e.reply(
        "`Success!\nYou are all set to use Google Drive with Ultroid Userbot.`",
        buttons=Button.inline("Main Menu", data="setter"),
    )


@callback("folderid", owner=True, func=lambda x: x.is_private)
async def _(e):
    if not e.is_private:
        return
    await e.edit(
        "Send your FOLDER ID\n\n"
        + "For FOLDER ID:\n"
        + "1. Open Google Drive App.\n"
        + "2. Create Folder.\n"
        + "3. Make that folder public.\n"
        + "4. Copy link of that folder.\n"
        + "5. Send all characters which is after id= .",
    )
    async with asst.conversation(e.sender_id) as conv:
        reply = conv.wait_event(events.NewMessage(from_users=e.sender_id))
        repl = await reply
        udB.set("GDRIVE_FOLDER_ID", repl.text)
        await repl.reply(
            "Success Now You Can Authorise.",
            buttons=get_back_button("gdrive"),
        )


@callback("clientsec", owner=True)
async def _(e):
    if not e.is_private:
        return
    await e.edit("Send your CLIENT SECRET")
    async with asst.conversation(e.sender_id) as conv:
        reply = conv.wait_event(events.NewMessage(from_users=e.sender_id))
        repl = await reply
        udB.set("GDRIVE_CLIENT_SECRET", repl.text)
        await repl.reply(
            "Success!\nNow You Can Authorise or add FOLDER ID.",
            buttons=get_back_button("gdrive"),
        )


@callback("clientid", owner=True)
async def _(e):
    if not e.is_private:
        return
    await e.edit("Send your CLIENT ID ending with .com")
    async with asst.conversation(e.sender_id) as conv:
        reply = conv.wait_event(events.NewMessage(from_users=e.sender_id))
        repl = await reply
        if not repl.text.endswith(".com"):
            return await repl.reply("`Wrong CLIENT ID`")
        udB.set("GDRIVE_CLIENT_ID", repl.text)
        await repl.reply(
            "Success now set CLIENT SECRET",
            buttons=get_back_button("gdrive"),
        )


@callback("gdrive", owner=True)
async def _(e):
    if not e.is_private:
        return
    await e.edit(
        "Go [here](https://console.developers.google.com/flows/enableapi?apiid=drive) and get your CLIENT ID and CLIENT SECRET",
        buttons=[
            [
                Button.inline("Cʟɪᴇɴᴛ Iᴅ", data="clientid"),
                Button.inline("Cʟɪᴇɴᴛ Sᴇᴄʀᴇᴛ", data="clientsec"),
            ],
            [
                Button.inline("Fᴏʟᴅᴇʀ Iᴅ", data="folderid"),
                Button.inline("Aᴜᴛʜᴏʀɪsᴇ", data="authorise"),
            ],
            [Button.inline("« Bᴀᴄᴋ", data="otvars")],
        ],
        link_preview=False,
    )


@callback("otvars", owner=True)
async def otvaar(event):
    await event.edit(
        "Other Variables to set for @TheUltroid:",
        buttons=[
            [
                Button.inline("Tᴀɢ Lᴏɢɢᴇʀ", data="taglog"),
                Button.inline("SᴜᴘᴇʀFʙᴀɴ", data="sfban"),
            ],
            [
                Button.inline("Sᴜᴅᴏ Mᴏᴅᴇ", data="sudo"),
                Button.inline("Hᴀɴᴅʟᴇʀ", data="hhndlr"),
            ],
            [
                Button.inline("Exᴛʀᴀ Pʟᴜɢɪɴs", data="plg"),
                Button.inline("Aᴅᴅᴏɴs", data="eaddon"),
            ],
            [
                Button.inline("Eᴍᴏᴊɪ ɪɴ Hᴇʟᴘ", data="emoj"),
                Button.inline("Sᴇᴛ ɢDʀɪᴠᴇ", data="gdrive"),
            ],
            [
                Button.inline("Iɴʟɪɴᴇ Pɪᴄ", data="inli_pic"),
                Button.inline("Sᴜᴅᴏ HNDLR", data="shndlr"),
            ],
            [Button.inline("Dᴜᴀʟ Mᴏᴅᴇ", "oofdm")],
            [Button.inline("« Bᴀᴄᴋ", data="setter")],
        ],
    )


@callback("oofdm", owner=True)
async def euwhe(event):
    BT = [
        [Button.inline("Dᴜᴀʟ Mᴏᴅᴇ Oɴ", "dmof")],
        [Button.inline("Dᴜᴀʟ Mᴏᴅᴇ Oғғ", "dmof")],
        [Button.inline("Dᴜᴀʟ Mᴏᴅᴇ Hɴᴅʟʀ", "dmhn")],
    ]
    await event.edit(
        "About [Dual Mode](https://t.me/UltroidUpdates/18)",
        buttons=BT,
        link_preview=False,
    )


@callback("dmof", owner=True)
async def rhwhe(e):
    if udB.get("DUAL_MODE"):
        udB.delete("DUAL_MODE")
        key = "Off"
    else:
        udB.set("DUAL_MODE", "True")
        key = "On"
    Msg = "Dual Mode : " + key
    await e.edit(Msg, buttons=get_back_button("otvars"))


@callback("dmhn", owner=True)
async def hndlrr(event):
    await event.delete()
    pru = event.sender_id
    var = "DUAL_HNDLR"
    name = "Dual Handler"
    CH = udB.get(var) or "/"
    async with event.client.conversation(pru) as conv:
        await conv.send_message(
            f"Send The Symbol Which u want as Handler/Trigger to use your Assistant bot\nUr Current Handler is [ `{CH}` ]\n\n use /cancel to cancel.",
        )
        response = conv.wait_event(events.NewMessage(chats=pru))
        response = await response
        themssg = response.message.message
        if themssg == "/cancel":
            await conv.send_message(
                "Cancelled!!",
                buttons=get_back_button("otvars"),
            )
        elif len(themssg) > 1:
            await conv.send_message(
                "Incorrect Handler",
                buttons=get_back_button("otvars"),
            )
        else:
            await setit(event, var, themssg)
            await conv.send_message(
                f"{name} changed to {themssg}",
                buttons=get_back_button("otvars"),
            )


@callback("emoj", owner=True)
async def emoji(event):
    await event.delete()
    pru = event.sender_id
    var = "EMOJI_IN_HELP"
    name = f"Emoji in `{HNDLR}help` menu"
    async with event.client.conversation(pru) as conv:
        await conv.send_message("Send emoji u want to set 🙃.\n\nUse /cancel to cancel.")
        response = conv.wait_event(events.NewMessage(chats=pru))
        response = await response
        themssg = response.message.message
        if themssg == "/cancel":
            await conv.send_message(
                "Cancelled!!",
                buttons=get_back_button("otvars"),
            )
        elif themssg.startswith(("/", HNDLR)):
            await conv.send_message(
                "Incorrect Emoji",
                buttons=get_back_button("otvars"),
            )
        else:
            await setit(event, var, themssg)
            await conv.send_message(
                f"{name} changed to {themssg}\n",
                buttons=get_back_button("otvars"),
            )


@callback("plg", owner=True)
async def pluginch(event):
    await event.delete()
    pru = event.sender_id
    var = "PLUGIN_CHANNEL"
    name = "Plugin Channel"
    async with event.client.conversation(pru) as conv:
        await conv.send_message(
            "Send id or username of a channel from where u want to install all plugins\n\nOur Channel~ @ultroidplugins\n\nUse /cancel to cancel.",
        )
        response = conv.wait_event(events.NewMessage(chats=pru))
        response = await response
        themssg = response.message.message
        if themssg == "/cancel":
            await conv.send_message(
                "Cancelled!!",
                buttons=get_back_button("otvars"),
            )
        elif themssg.startswith(("/", HNDLR)):
            await conv.send_message(
                "Incorrect channel",
                buttons=get_back_button("otvars"),
            )
        else:
            await setit(event, var, themssg)
            await conv.send_message(
                "{} changed to {}\n After Setting All Things Do Restart".format(
                    name,
                    themssg,
                ),
                buttons=get_back_button("otvars"),
            )


@callback("hhndlr", owner=True)
async def hndlrr(event):
    await event.delete()
    pru = event.sender_id
    var = "HNDLR"
    name = "Handler/ Trigger"
    async with event.client.conversation(pru) as conv:
        await conv.send_message(
            f"Send The Symbol Which u want as Handler/Trigger to use bot\nUr Current Handler is [ `{HNDLR}` ]\n\n use /cancel to cancel.",
        )
        response = conv.wait_event(events.NewMessage(chats=pru))
        response = await response
        themssg = response.message.message
        if themssg == "/cancel":
            await conv.send_message(
                "Cancelled!!",
                buttons=get_back_button("otvars"),
            )
        elif len(themssg) > 1:
            await conv.send_message(
                "Incorrect Handler",
                buttons=get_back_button("otvars"),
            )
        elif themssg.startswith(("/", "#", "@")):
            await conv.send_message(
                "This cannot be used as handler",
                buttons=get_back_button("otvars"),
            )
        else:
            await setit(event, var, themssg)
            await conv.send_message(
                f"{name} changed to {themssg}",
                buttons=get_back_button("otvars"),
            )


@callback("shndlr", owner=True)
async def hndlrr(event):
    await event.delete()
    pru = event.sender_id
    var = "SUDO_HNDLR"
    name = "Sudo Handler"
    async with event.client.conversation(pru) as conv:
        await conv.send_message(
            "Send The Symbol Which u want as Sudo Handler/Trigger to use bot\n\n use /cancel to cancel."
        )

        response = conv.wait_event(events.NewMessage(chats=pru))
        response = await response
        themssg = response.message.message
        if themssg == "/cancel":
            await conv.send_message(
                "Cancelled!!",
                buttons=get_back_button("otvars"),
            )
        elif len(themssg) > 1:
            await conv.send_message(
                "Incorrect Handler",
                buttons=get_back_button("otvars"),
            )
        elif themssg.startswith(("/", "#", "@")):
            await conv.send_message(
                "This cannot be used as handler",
                buttons=get_back_button("otvars"),
            )
        else:
            await setit(event, var, themssg)
            await conv.send_message(
                f"{name} changed to {themssg}",
                buttons=get_back_button("otvars"),
            )


@callback("taglog", owner=True)
async def tagloggrr(e):
    if not udB.get("TAG_LOG"):
        BUTTON = [Button.inline("SET TAG LOG", data="settag")]
    else:
        BUTTON = [Button.inline("DELETE TAG LOG", data="deltag")]
    await e.edit(
        "Choose Options",
        buttons=[BUTTON, [Button.inline("« Bᴀᴄᴋ", data="otvars")]],
    )


@callback("deltag", owner=True)
async def _(e):
    udB.delete("TAG_LOG")
    await e.answer("Done!!! TAG lOG Off")


@callback("settag", owner=True)
async def taglogerr(event):
    await event.delete()
    pru = event.sender_id
    var = "TAG_LOG"
    name = "Tag Log Group"
    async with event.client.conversation(pru) as conv:
        await conv.send_message(
            f"Make a group, add your assistant and make it admin.\nGet the `{HNDLR}id` of that group and send it here for tag logs.\n\nUse /cancel to cancel.",
        )
        response = conv.wait_event(events.NewMessage(chats=pru))
        response = await response
        themssg = response.message.message
        if themssg == "/cancel":
            return await conv.send_message(
                "Cancelled!!",
                buttons=get_back_button("taglog"),
            )
        await setit(event, var, themssg)
        await conv.send_message(
            f"{name} changed to {themssg}",
            buttons=get_back_button("taglog"),
        )


@callback("eaddon", owner=True)
async def pmset(event):
    if not udB.get("ADDONS"):
        BT = [Button.inline("Aᴅᴅᴏɴs  Oɴ", data="edon")]
    else:
        BT = [Button.inline("Aᴅᴅᴏɴs  Oғғ", data="edof")]
    await event.edit(
        "ADDONS~ Extra Plugins:",
        buttons=[
            BT,
            [Button.inline("« Bᴀᴄᴋ", data="otvars")],
        ],
    )


@callback("edon", owner=True)
async def eddon(event):
    var = "ADDONS"
    await setit(event, var, "True")
    await event.edit(
        "Done! ADDONS has been turned on!!\n\n After Setting All Things Do Restart",
        buttons=get_back_button("eaddon"),
    )


@callback("edof", owner=True)
async def eddof(event):
    udB.set("ADDONS", "False")
    await event.edit(
        "Done! ADDONS has been turned off!! After Setting All Things Do Restart",
        buttons=get_back_button("eaddon"),
    )


@callback("sudo", owner=True)
async def pmset(event):
    if not udB.get("SUDO"):
        BT = [Button.inline("Sᴜᴅᴏ Mᴏᴅᴇ  Oɴ", data="onsudo")]
    else:
        BT = [Button.inline("Sᴜᴅᴏ Mᴏᴅᴇ  Oғғ", data="ofsudo")]
    await event.edit(
        f"SUDO MODE ~ Some peoples can use ur Bot which u selected. To know More use `{HNDLR}help sudo`",
        buttons=[
            BT,
            [Button.inline("« Bᴀᴄᴋ", data="otvars")],
        ],
    )


@callback("onsudo", owner=True)
async def eddon(event):
    var = "SUDO"
    await setit(event, var, "True")
    await event.edit(
        "Done! SUDO MODE has been turned on!!\n\n After Setting All Things Do Restart",
        buttons=get_back_button("sudo"),
    )


@callback("ofsudo", owner=True)
async def eddof(event):
    var = "SUDO"
    await setit(event, var, "False")
    await event.edit(
        "Done! SUDO MODE has been turned off!! After Setting All Things Do Restart",
        buttons=get_back_button("sudo"),
    )


@callback("sfban", owner=True)
async def sfban(event):
    await event.edit(
        "SuperFban Settings:",
        buttons=[
            [Button.inline("FBᴀɴ Gʀᴏᴜᴘ", data="sfgrp")],
            [Button.inline("Exᴄʟᴜᴅᴇ Fᴇᴅs", data="sfexf")],
            [Button.inline("« Bᴀᴄᴋ", data="otvars")],
        ],
    )


@callback("sfgrp", owner=True)
async def sfgrp(event):
    await event.delete()
    name = "FBan Group ID"
    var = "FBAN_GROUP_ID"
    pru = event.sender_id
    async with asst.conversation(pru) as conv:
        await conv.send_message(
            f"Make a group, add @MissRose_Bot, send `{HNDLR}id`, copy that and send it here.\nUse /cancel to go back.",
        )
        response = conv.wait_event(events.NewMessage(chats=pru))
        response = await response
        themssg = response.message.message
        if themssg == "/cancel":
            return await conv.send_message(
                "Cancelled!!",
                buttons=get_back_button("sfban"),
            )
        await setit(event, var, themssg)
        await conv.send_message(
            f"{name} changed to {themssg}",
            buttons=get_back_button("sfban"),
        )


@callback("sfexf", owner=True)
async def sfexf(event):
    await event.delete()
    name = "Excluded Feds"
    var = "EXCLUDE_FED"
    pru = event.sender_id
    async with asst.conversation(pru) as conv:
        await conv.send_message(
            "Send the Fed IDs you want to exclude in the ban. Split by a space.\neg`id1 id2 id3`\nSet is as `None` if you dont want any.\nUse /cancel to go back."
        )

        response = conv.wait_event(events.NewMessage(chats=pru))
        response = await response
        themssg = response.message.message
        if themssg == "/cancel":
            return await conv.send_message(
                "Cancelled!!",
                buttons=get_back_button("sfban"),
            )
        await setit(event, var, themssg)
        await conv.send_message(
            f"{name} changed to {themssg}",
            buttons=get_back_button("sfban"),
        )


@callback("alvcstm", owner=True)
async def alvcs(event):
    await event.edit(
        f"Customise your {HNDLR}alive. Choose from the below options -",
        buttons=[
            [Button.inline("Aʟɪᴠᴇ Tᴇxᴛ", data="alvtx")],
            [Button.inline("Aʟɪᴠᴇ ᴍᴇᴅɪᴀ", data="alvmed")],
            [Button.inline("Dᴇʟᴇᴛᴇ Aʟɪᴠᴇ Mᴇᴅɪᴀ", data="delmed")],
            [Button.inline("« Bᴀᴄᴋ", data="setter")],
        ],
    )


@callback("alvtx", owner=True)
async def name(event):
    await event.delete()
    pru = event.sender_id
    var = "ALIVE_TEXT"
    name = "Alive Text"
    async with event.client.conversation(pru) as conv:
        await conv.send_message(
            "**Alive Text**\nEnter the new alive text.\n\nUse /cancel to terminate the operation.",
        )
        response = conv.wait_event(events.NewMessage(chats=pru))
        response = await response
        themssg = response.message.message
        if themssg == "/cancel":
            return await conv.send_message(
                "Cancelled!!",
                buttons=get_back_button("alvcstm"),
            )
        await setit(event, var, themssg)
        await conv.send_message(
            "{} changed to {}\n\nAfter Setting All Things Do restart".format(
                name,
                themssg,
            ),
            buttons=get_back_button("alvcstm"),
        )


@callback("alvmed", owner=True)
async def media(event):
    await event.delete()
    pru = event.sender_id
    var = "ALIVE_PIC"
    name = "Alive Media"
    async with event.client.conversation(pru) as conv:
        await conv.send_message(
            "**Alive Media**\nSend me a pic/gif/media to set as alive media.\n\nUse /cancel to terminate the operation.",
        )
        response = await conv.get_response()
        try:
            themssg = response.message.message
            if themssg == "/cancel":
                return await conv.send_message(
                    "Operation cancelled!!",
                    buttons=get_back_button("alvcstm"),
                )
        except BaseException:
            pass
        if (
            not (response.text).startswith("/")
            and response.text != ""
            and (not response.media or isinstance(response.media, MessageMediaWebPage))
        ):
            url = text_to_url(response)
        elif response.sticker:
            url = response.file.id
        else:
            media = await event.client.download_media(response, "alvpc")
            try:
                x = upl(media)
                url = f"https://telegra.ph/{x[0]}"
                remove(media)
            except BaseException:
                return await conv.send_message(
                    "Terminated.",
                    buttons=get_back_button("alvcstm"),
                )
        await setit(event, var, url)
        await conv.send_message(
            f"{name} has been set.",
            buttons=get_back_button("alvcstm"),
        )


@callback("delmed", owner=True)
async def dell(event):
    try:
        udB.delete("ALIVE_PIC")
        return await event.edit(
            get_string("clst_5"), buttons=get_back_button("alvcstm")
        )
    except BaseException:
        return await event.edit(
            get_string("clst_4"),
            buttons=get_back_button("alvcstm"),
        )


@callback("pmcstm", owner=True)
async def alvcs(event):
    await event.edit(
        "Customise your PMPERMIT Settings -",
        buttons=[
            [
                Button.inline("Pᴍ Tᴇxᴛ", data="pmtxt"),
                Button.inline("Pᴍ Mᴇᴅɪᴀ", data="pmmed"),
            ],
            [
                Button.inline("Aᴜᴛᴏ Aᴘᴘʀᴏᴠᴇ", data="apauto"),
                Button.inline("PMLOGGER", data="pml"),
            ],
            [
                Button.inline("Sᴇᴛ Wᴀʀɴs", data="swarn"),
                Button.inline("Dᴇʟᴇᴛᴇ Pᴍ Mᴇᴅɪᴀ", data="delpmmed"),
            ],
            [Button.inline("PMPermit Type", data="pmtype")],
            [Button.inline("« Bᴀᴄᴋ", data="ppmset")],
        ],
    )


@callback("pmtype", owner=True)
async def pmtyp(event):
    await event.edit(
        "Select the type of PMPermit needed.",
        buttons=[
            [Button.inline("Inline", data="inpm_in")],
            [Button.inline("Normal", data="inpm_no")],
            [Button.inline("« Bᴀᴄᴋ", data="pmcstm")],
        ],
    )


@callback("inpm_in", owner=True)
async def inl_on(event):
    var = "INLINE_PM"
    await setit(event, var, "True")
    await event.edit(
        "Done!! PMPermit type has been set to inline!",
        buttons=[[Button.inline("« Bᴀᴄᴋ", data="pmtype")]],
    )


@callback("inpm_no", owner=True)
async def inl_on(event):
    var = "INLINE_PM"
    await setit(event, var, "False")
    await event.edit(
        "Done!! PMPermit type has been set to normal!",
        buttons=[[Button.inline("« Bᴀᴄᴋ", data="pmtype")]],
    )


@callback("pmtxt", owner=True)
async def name(event):
    await event.delete()
    pru = event.sender_id
    var = "PM_TEXT"
    name = "PM Text"
    async with event.client.conversation(pru) as conv:
        await conv.send_message(
            "**PM Text**\nEnter the new Pmpermit text.\n\nu can use `{name}` `{fullname}` `{count}` `{mention}` `{username}` to get this from user Too\n\nUse /cancel to terminate the operation.",
        )
        response = conv.wait_event(events.NewMessage(chats=pru))
        response = await response
        themssg = response.message.message
        if themssg == "/cancel":
            return await conv.send_message(
                "Cancelled!!",
                buttons=get_back_button("pmcstm"),
            )
        if len(themssg) > 4090:
            return await conv.send_message(
                "Message too long!\nGive a shorter message please!!",
                buttons=get_back_button("pmcstm"),
            )
        await setit(event, var, themssg)
        await conv.send_message(
            "{} changed to {}\n\nAfter Setting All Things Do restart".format(
                name,
                themssg,
            ),
            buttons=get_back_button("pmcstm"),
        )


@callback("swarn", owner=True)
async def name(event):
    m = range(1, 10)
    tultd = [Button.inline(f"{x}", data=f"wrns_{x}") for x in m]
    lst = list(zip(tultd[::3], tultd[1::3], tultd[2::3]))
    lst.append([Button.inline("« Bᴀᴄᴋ", data="pmcstm")])
    await event.edit(
        "Select the number of warnings for a user before getting blocked in PMs.",
        buttons=lst,
    )


@callback(re.compile(b"wrns_(.*)"), owner=True)
async def set_wrns(event):
    value = int(event.data_match.group(1).decode("UTF-8"))
    dn = udB.set("PMWARNS", value)
    if dn:
        await event.edit(
            f"PM Warns Set to {value}.\nNew users will have {value} chances in PMs before getting banned.",
            buttons=get_back_button("pmcstm"),
        )
    else:
        await event.edit(
            f"Something went wrong, please check your {HNDLR}logs!",
            buttons=get_back_button("pmcstm"),
        )


@callback("pmmed", owner=True)
async def media(event):
    await event.delete()
    pru = event.sender_id
    var = "PMPIC"
    name = "PM Media"
    async with event.client.conversation(pru) as conv:
        await conv.send_message(
            "**PM Media**\nSend me a pic/gif/sticker/link  to set as pmpermit media.\n\nUse /cancel to terminate the operation.",
        )
        response = await conv.get_response()
        try:
            themssg = response.message.message
            if themssg == "/cancel":
                return await conv.send_message(
                    "Operation cancelled!!",
                    buttons=get_back_button("pmcstm"),
                )
        except BaseException:
            pass
        media = await event.client.download_media(response, "pmpc")
        if (
            not (response.text).startswith("/")
            and response.text != ""
            and (not response.media or isinstance(response.media, MessageMediaWebPage))
        ):
            url = text_to_url(response)
        elif response.sticker:
            url = response.file.id
        else:
            try:
                x = upl(media)
                url = f"https://telegra.ph/{x[0]}"
                remove(media)
            except BaseException:
                return await conv.send_message(
                    "Terminated.",
                    buttons=get_back_button("pmcstm"),
                )
        await setit(event, var, url)
        await conv.send_message(
            f"{name} has been set.",
            buttons=get_back_button("pmcstm"),
        )


@callback("delpmmed", owner=True)
async def dell(event):
    try:
        udB.delete("PMPIC")
        return await event.edit(get_string("clst_5"), buttons=get_back_button("pmcstm"))
    except BaseException:
        return await event.edit(
            get_string("clst_4"),
            buttons=[[Button.inline("« Sᴇᴛᴛɪɴɢs", data="setter")]],
        )


@callback("apauto", owner=True)
async def apauto(event):
    await event.edit(
        "This'll auto approve on outgoing messages",
        buttons=[
            [Button.inline("Aᴜᴛᴏ Aᴘᴘʀᴏᴠᴇ ON", data="apon")],
            [Button.inline("Aᴜᴛᴏ Aᴘᴘʀᴏᴠᴇ OFF", data="apof")],
            [Button.inline("« Bᴀᴄᴋ", data="pmcstm")],
        ],
    )


@callback("apon", owner=True)
async def apon(event):
    var = "AUTOAPPROVE"
    await setit(event, var, "True")
    await event.edit(
        "Done!! AUTOAPPROVE  Started!!",
        buttons=[[Button.inline("« Bᴀᴄᴋ", data="apauto")]],
    )


@callback("apof", owner=True)
async def apof(event):
    try:
        udB.delete("AUTOAPPROVE")
        return await event.edit(
            "Done! AUTOAPPROVE Stopped!!",
            buttons=[[Button.inline("« Bᴀᴄᴋ", data="apauto")]],
        )
    except BaseException:
        return await event.edit(
            get_string("clst_4"),
            buttons=[[Button.inline("« Sᴇᴛᴛɪɴɢs", data="setter")]],
        )


@callback("pml", owner=True)
async def alvcs(event):
    if not udB.get("PMLOG"):
        BT = [Button.inline("PMLOGGER ON", data="pmlog")]
    else:
        BT = [Button.inline("PMLOGGER OFF", data="pmlogof")]
    await event.edit(
        "PMLOGGER This Will Forward Ur Pm to Ur Private Group -",
        buttons=[
            BT,
            [Button.inline("PᴍLᴏɢɢᴇʀ Gʀᴏᴜᴘ", "pmlgg")],
            [Button.inline("« Bᴀᴄᴋ", data="pmcstm")],
        ],
    )


@callback("pmlgg", owner=True)
async def disus(event):
    await event.delete()
    pru = event.sender_id
    var = "PMLOGGROUP"
    name = "Pm Logger Group"
    async with event.client.conversation(pru) as conv:
        await conv.send_message(
            f"Send The Chat Id of group Which u want as your {name}\n\n use /cancel to cancel.",
        )
        response = conv.wait_event(events.NewMessage(chats=pru))
        response = await response
        themssg = response.message.message
        if themssg == "/cancel":
            await conv.send_message(
                "Cancelled!!",
                buttons=get_back_button("pml"),
            )
        else:
            await setit(event, var, themssg)
            await conv.send_message(
                f"{name} changed to `{themssg}`",
                buttons=get_back_button("pml"),
            )


@callback("pmlog", owner=True)
async def pmlog(event):
    await setit(event, "PMLOG", "True")
    await event.edit(
        "Done!! PMLOGGER  Started!!",
        buttons=[[Button.inline("« Bᴀᴄᴋ", data="pml")]],
    )


@callback("pmlogof", owner=True)
async def pmlogof(event):
    try:
        udB.delete("PMLOG")
        return await event.edit(
            "Done! PMLOGGER Stopped!!",
            buttons=[[Button.inline("« Bᴀᴄᴋ", data="pml")]],
        )
    except BaseException:
        return await event.edit(
            get_string("clst_4"),
            buttons=[[Button.inline("« Sᴇᴛᴛɪɴɢs", data="setter")]],
        )


@callback("ppmset", owner=True)
async def pmset(event):
    await event.edit(
        "PMPermit Settings:",
        buttons=[
            [Button.inline("Tᴜʀɴ PMPᴇʀᴍɪᴛ Oɴ", data="pmon")],
            [Button.inline("Tᴜʀɴ PMPᴇʀᴍɪᴛ Oғғ", data="pmoff")],
            [Button.inline("Cᴜsᴛᴏᴍɪᴢᴇ PMPᴇʀᴍɪᴛ", data="pmcstm")],
            [Button.inline("« Bᴀᴄᴋ", data="setter")],
        ],
    )


@callback("pmon", owner=True)
async def pmonn(event):
    var = "PMSETTING"
    await setit(event, var, "True")
    await event.edit(
        "Done! PMPermit has been turned on!!",
        buttons=[[Button.inline("« Bᴀᴄᴋ", data="ppmset")]],
    )


@callback("pmoff", owner=True)
async def pmofff(event):
    var = "PMSETTING"
    await setit(event, var, "False")
    await event.edit(
        "Done! PMPermit has been turned off!!",
        buttons=[[Button.inline("« Bᴀᴄᴋ", data="ppmset")]],
    )


@callback("botmew", owner=True)
async def hhh(e):
    async with e.client.conversation(e.chat_id) as conv:
        await conv.send_message("Send Any Media to keep at your Bot's welcome ")
        msg = await conv.get_response()
        if not msg.media or msg.text.startswith("/"):
            return await conv.send_message(
                "Terminated!", buttons=get_back_button("chatbot")
            )
        udB.set("STARTMEDIA", msg.file.id)
        await conv.send_message("Done!", buttons=get_back_button("chatbot"))


@callback("chatbot", owner=True)
async def chbot(event):
    await event.edit(
        "From This Feature U can chat with ppls Via ur Assistant Bot.\n[More info](https://t.me/UltroidUpdates/2)",
        buttons=[
            [Button.inline("Cʜᴀᴛ Bᴏᴛ  Oɴ", data="onchbot")],
            [Button.inline("Cʜᴀᴛ Bᴏᴛ  Oғғ", data="ofchbot")],
            [Button.inline("Bᴏᴛ Wᴇʟᴄᴏᴍᴇ", data="bwel")],
            [Button.inline("Bᴏᴛ Wᴇʟᴄᴏᴍᴇ Mᴇᴅɪᴀ", data="botmew")],
            [Button.inline("Bᴏᴛ Iɴғᴏ Tᴇxᴛ", data="botinfe")],
            [Button.inline("Fᴏʀᴄᴇ Sᴜʙsᴄʀɪʙᴇ", data="pmfs")],
            [Button.inline("« Bᴀᴄᴋ", data="setter")],
        ],
        link_preview=False,
    )


@callback("botinfe", owner=True)
async def hhh(e):
    async with e.client.conversation(e.chat_id) as conv:
        await conv.send_message(
            "Send message to set to Display, when user Press Info button in Bot Welcome!\n\nsend `False` to completely remove that button.."
        )
        msg = await conv.get_response()
        if msg.media or msg.text.startswith("/"):
            return await conv.send_message(
                "Terminated!", buttons=get_back_button("chatbot")
            )
        udB.set("BOT_INFO_START", msg.text)
        await conv.send_message("Done!", buttons=get_back_button("chatbot"))


@callback("pmfs", owner=True)
async def heheh(event):
    Ll = []
    err = ""
    async with event.client.conversation(event.chat_id) as conv:
        await conv.send_message(
            "• Send The Chat Id(s), which you want user to Join Before using Chat/Pm Bot"
        )
        await conv.send_message(
            "Example : \n`-1001234567\n-100778888`\n\nFor Multiple Chat(s)."
        )
        try:
            msg = await conv.get_response()
        except AsyncTimeOut:
            return await conv.send_message("TimeUp!\nStart from /start back.")
        if not msg.text or msg.text.startswith("/"):
            return await conv.send_message(
                "Cancelled!", buttons=get_back_button("chatbot")
            )
        for chat in msg.message.split("\n"):
            if chat.startswith("-") or chat.isdigit():
                chat = int(chat)
            try:
                CHSJSHS = await event.client.get_entity(chat)
                Ll.append(get_peer_id(CHSJSHS))
            except Exception as er:
                err += f"**{chat}** : {er}\n"
        if err:
            return await conv.send_message(err)
        udB.set("PMBOT_FSUB", str(Ll))
        await conv.send_message(
            "Done!\nRestart Your Bot.", buttons=get_back_button("chatbot")
        )


@callback("bwel", owner=True)
async def name(event):
    await event.delete()
    pru = event.sender_id
    var = "STARTMSG"
    name = "Bot Welcome Message:"
    async with event.client.conversation(pru) as conv:
        await conv.send_message(
            "**BOT WELCOME MSG**\nEnter the msg which u want to show when someone start your assistant Bot.\nYou Can use `{me}` , `{mention}` Parameters Too\nUse /cancel to terminate the operation.",
        )
        response = conv.wait_event(events.NewMessage(chats=pru))
        response = await response
        themssg = response.message.message
        if themssg == "/cancel":
            return await conv.send_message(
                "Cancelled!!",
                buttons=get_back_button("chatbot"),
            )
        await setit(event, var, themssg)
        await conv.send_message(
            "{} changed to {}".format(
                name,
                themssg,
            ),
            buttons=get_back_button("chatbot"),
        )


@callback("onchbot", owner=True)
async def chon(event):
    var = "PMBOT"
    await setit(event, var, "True")
    Loader(path="assistant/pmbot.py", key="PM Bot").load_single()
    if AST_PLUGINS.get("pmbot"):
        for i, e in AST_PLUGINS["pmbot"]:
            event.client.remove_event_handler(i)
        for i, e in AST_PLUGINS["pmbot"]:
            event.client.add_event_handler(i, events.NewMessage(**e))
    await event.edit(
        "Done! Now u Can Chat With People Via This Bot",
        buttons=[Button.inline("« Bᴀᴄᴋ", data="chatbot")],
    )


@callback("ofchbot", owner=True)
async def chon(event):
    var = "PMBOT"
    await setit(event, var, "False")
    if AST_PLUGINS.get("pmbot"):
        for i, e in AST_PLUGINS["pmbot"]:
            event.client.remove_event_handler(i)
    await event.edit(
        "Done! Chat People Via This Bot Stopped.",
        buttons=[Button.inline("« Bᴀᴄᴋ", data="chatbot")],
    )


@callback("vcb", owner=True)
async def vcb(event):
    await event.edit(
        "From This Feature U can play songs in group voice chat\n\n[moreinfo](https://t.me/UltroidUpdates/4)",
        buttons=[
            [Button.inline("VC Sᴇssɪᴏɴ", data="vcs")],
            [Button.inline("« Bᴀᴄᴋ", data="setter")],
        ],
        link_preview=False,
    )


@callback("vcs", owner=True)
async def name(event):
    await event.delete()
    pru = event.sender_id
    var = "VC_SESSION"
    name = "VC SESSION"
    async with event.client.conversation(pru) as conv:
        await conv.send_message(
            "**Vc session**\nEnter the New session u generated for vc bot.\n\nUse /cancel to terminate the operation.",
        )
        response = conv.wait_event(events.NewMessage(chats=pru))
        response = await response
        themssg = response.message.message
        if themssg == "/cancel":
            return await conv.send_message(
                "Cancelled!!",
                buttons=get_back_button("vcb"),
            )
        await setit(event, var, themssg)
        await conv.send_message(
            "{} changed to {}\n\nAfter Setting All Things Do restart".format(
                name,
                themssg,
            ),
            buttons=get_back_button("vcb"),
        )


@callback("inli_pic", owner=True)
async def media(event):
    await event.delete()
    pru = event.sender_id
    var = "INLINE_PIC"
    name = "Inline Media"
    async with event.client.conversation(pru) as conv:
        await conv.send_message(
            "**Inline Media**\nSend me a pic/gif/ or link  to set as inline media.\n\nUse /cancel to terminate the operation.",
        )
        response = await conv.get_response()
        try:
            themssg = response.message.message
            if themssg == "/cancel":
                return await conv.send_message(
                    "Operation cancelled!!",
                    buttons=get_back_button("setter"),
                )
        except BaseException:
            pass
        media = await event.client.download_media(response, "inlpic")
        if (
            not (response.text).startswith("/")
            and response.text != ""
            and (not response.media or isinstance(response.media, MessageMediaWebPage))
        ):
            url = text_to_url(response)
        else:
            try:
                x = upl(media)
                url = f"https://telegra.ph/{x[0]}"
                remove(media)
            except BaseException:
                return await conv.send_message(
                    "Terminated.",
                    buttons=get_back_button("setter"),
                )
        await setit(event, var, url)
        await conv.send_message(
            f"{name} has been set.",
            buttons=get_back_button("setter"),
        )
