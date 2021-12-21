# Ultroid - UserBot
# Copyright (C) 2021 TeamUltroid
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ >
# PLease read the GNU Affero General Public License in
# <https://www.github.com/TeamUltroid/Ultroid/blob/main/LICENSE/>.

import re

from . import *

STRINGS = {
    1: """🎇 **Thanks for Deploying SlapTap Userbot!**

• Here, are the Some Basic stuff from, where you can Know, about its Usage.""",
    2: """🎉** About SlapTap**

🧿 SlapTap is Pluggable and powerful Telethon Userbot, made in Python from Scratch. It is Aimed to Increase Security along with Addition of Other Useful Features.

❣ Made by **@SlapTap**""",
    3: """**💡• FAQs •**

-> [Username Tracker](https://t.me/SlapTap/11)
-> [Keeping Custom Addons Repo](https://t.me/SlapTap/12)
-> [Disabling Deploy message](https://t.me/SlapTap/13)
-> [Setting up TimeZone](https://t.me/SlapTap/14)
-> [About Inline PmPermit](https://t.me/SlapTap/15)
-> [About Dual Mode](https://t.me/SlapTap/16)
-> [Custom Thumbnail](https://t.me/SlapTap/17)
-> [About FullSudo](https://t.me/SlapTap/18)
-> [Setting Up PmBot](https://t.me/SlapTap/19)
-> [Also Check](https://t.me/SlapTap/20)

**• To Know About Updates**
  - Join @SlapTap.""",
    4: f"""• `To Know All Available Commands`

  - `{HNDLR}help`
  - `{HNDLR}cmds`""",
    5: """• **For Any Other Query or Suggestion**
  - Move to **@SlapTaps**.

• Thanks for Reaching till END.""",
}


@callback(re.compile("initft_(\\d+)"))
async def init_depl(e):
    CURRENT = int(e.data_match.group(1))
    if CURRENT == 5:
        return await e.edit(
            STRINGS[5],
            buttons=Button.inline("<< Back", "initbk_" + str(4)),
            link_preview=False,
        )
    await e.edit(
        STRINGS[CURRENT],
        buttons=[
            Button.inline("<<", "initbk_" + str(CURRENT - 1)),
            Button.inline(">>", "initft_" + str(CURRENT + 1)),
        ],
        link_preview=False,
    )


@callback(re.compile("initbk_(\\d+)"))
async def ineiq(e):
    CURRENT = int(e.data_match.group(1))
    if CURRENT == 1:
        return await e.edit(
            STRINGS[1],
            buttons=Button.inline("Start Back >>", "initft_" + str(2)),
            link_preview=False,
        )
    await e.edit(
        STRINGS[CURRENT],
        buttons=[
            Button.inline("<<", "initbk_" + str(CURRENT - 1)),
            Button.inline(">>", "initft_" + str(CURRENT + 1)),
        ],
        link_preview=False,
    )
