import random
import asyncio
import importlib
import io
from pathlib import Path
from os import path
from nonebot import on_command
import pygtrie
from nonebot.matcher import Matcher
from nonebot.params import ArgPlainText
from nonebot.adapters import Event, Bot
from nonebot.typing import T_State
from async_timeout import timeout

from PIL import Image, ImageDraw, ImageFont
from nonebot_plugin_saa import MessageFactory
from nonebot_plugin_saa import Image as saaImage
from . import poke_data
from .utils.convert import DailyAmountLimiter
from .utils.dbbase.GameCounter import GAME_DB
from .utils.dbbase.ScoreCounter import SCORE_DB
from .utils.dbbase.PokeCounter import PokeCounter
from .utils.resource.RESOURCE_PATH import CHAR_ICON_PATH

PIC_SIDE_LENGTH = 25
LH_SIDE_LENGTH = 75
ONE_TURN_TIME = 20
WHOIS_NUM = 6
daily_whois_limiter = DailyAmountLimiter("whois", WHOIS_NUM, 0)
FILE_PATH = Path(__file__).parent
FONTS_PATH = Path(FILE_PATH / "font")
FONTS_PATH = Path(FONTS_PATH / "sakura.ttf")


class WinnerJudger:
    def __init__(self):
        self.on = {}
        self.winner = {}
        self.correct_chara_id = {}
        self.correct_win_pic = {}

    def record_winner(self, gid, uid):
        self.winner[gid] = str(uid)

    def get_winner(self, gid):
        return self.winner[gid] if self.winner.get(gid) is not None else ""

    def get_on_off_status(self, gid):
        return self.on[gid] if self.on.get(gid) is not None else False

    def set_correct_win_pic(self, gid, pic):
        self.correct_win_pic[gid] = pic

    def get_correct_win_pic(self, gid):
        return self.correct_win_pic[gid]

    def set_correct_chara_id(self, gid, cid):
        self.correct_chara_id[gid] = cid

    def get_correct_chara_id(self, gid):
        return (
            self.correct_chara_id[gid]
            if self.correct_chara_id.get(gid) is not None
            else 9999
        )

    def turn_on(self, gid):
        self.on[gid] = True

    def turn_off(self, gid):
        self.on[gid] = False
        self.winner[gid] = ""
        self.correct_chara_id[gid] = 9999


winner_judger = WinnerJudger()


class Roster:
    def __init__(self):
        self._roster = pygtrie.CharTrie()
        self.update()

    def update(self):
        importlib.reload(poke_data)
        self._roster.clear()
        for idx, names in poke_data.CHARA_NAME.items():
            for n in names:
                if n not in self._roster:
                    self._roster[n] = idx
        self._all_name_list = self._roster.keys()

    def get_id(self, name):
        return self._roster[name] if name in self._roster else 9999


roster = Roster()


async def get_win_pic(name, enname):
    im = Image.new("RGB", (640, 464), (255, 255, 255))
    base_img = path.join(FILE_PATH, "whois_bg.jpg")
    dtimg = Image.open(base_img)
    dtbox = (0, 0)
    im.paste(dtimg, dtbox)
    image = Image.open(CHAR_ICON_PATH / f"{name}.png").convert("RGBA")
    image = image.resize((230, 230))
    dtbox = (50, 60)
    im.paste(image, dtbox, mask=image.split()[3])

    draw = ImageDraw.Draw(im)
    line = enname
    font = ImageFont.truetype(FONTS_PATH, 40)
    draw.text(
        (470, 40),
        line,
        (255, 255, 0),
        font,
        "mm",
    )

    line = name
    font = ImageFont.truetype(FONTS_PATH, 42)
    draw.text(
        (470, 100),
        line,
        (255, 255, 0),
        font,
        "mm",
    )
    img = await convert_img(im)
    return img


who_is = on_command("我是谁", aliases={"whois"}, priority=5, block=True)


@who_is.handle()
async def pokemon_whois(ev: Event, matcher: Matcher, state: T_State):
    if winner_judger.get_on_off_status(ev.get_session_id()):
        await matcher.send("此轮游戏还没结束，请勿重复使用指令")
        return
    winner_judger.turn_on(ev.get_session_id())
    chara_id_list = list(poke_data.CHARA_NAME.keys())
    poke_list = poke_data.CHARA_NAME
    random.shuffle(chara_id_list)
    winner_judger.set_correct_chara_id(ev.get_session_id(), chara_id_list[0])
    # print(chara_id_list[0])

    name = poke_list[chara_id_list[0]][0]
    enname = poke_list[chara_id_list[0]][1]
    win_mes = await get_win_pic(name, enname)
    winner_judger.set_correct_win_pic(ev.get_session_id(), win_mes)
    print(name)
    state["name"] = name
    im = Image.new("RGB", (640, 464), (255, 255, 255))
    base_img = path.join(FILE_PATH, "whois_bg.jpg")
    dtimg = Image.open(base_img)
    dtbox = (0, 0)
    im.paste(dtimg, dtbox)

    image = Image.open(CHAR_ICON_PATH / f"{name}.png").convert("RGBA")
    image = image.resize((230, 230))
    width = image.size[0]  # 获取图片宽度
    height = image.size[1]  # 获取图片高度
    for x in range(width):
        for y in range(height):
            R, G, B, A = image.getpixel((x, y))  # 获取单个像素点的RGB

            """转化为灰度：整数方法"""
            if A == 0:
                Gray = 255
            else:
                Gray = 0
                A = 255
            # if x == 0 and y == 0:
            # print(str(rgba))
            # print("R:"+str(R))
            # print("G:"+str(G))
            # print("B:"+str(B))
            # print("A:"+str(A))
            # print("Gray:"+str(Gray))
            """转化为灰度图：GRB(Gray,Gray,Gray)替换GRB(R,G,B)"""
            image.putpixel((x, y), (Gray, Gray, Gray, A))
    """保存灰度图"""
    image = image.convert("RGBA")
    dtbox = (50, 60)
    im.paste(image, dtbox, mask=image.split()[3])

    draw = ImageDraw.Draw(im)
    line = "？？？"
    font = ImageFont.truetype(FONTS_PATH, 40)
    draw.text(
        (470, 40),
        line,
        (255, 255, 0),
        font,
        "mm",
    )

    line = "我是谁"
    font = ImageFont.truetype(FONTS_PATH, 42)
    draw.text(
        (470, 100),
        line,
        (255, 255, 0),
        font,
        "mm",
    )
    img = await convert_img(im)
    # output = BytesIO()
    # im.save(output, format="PNG")
    # base64_str = 'base64://' + base64.b64encode(output.getvalue()).decode()
    mesg_a = []
    mes = f"猜猜我是谁，({ONE_TURN_TIME}s后公布答案)"
    mesg_a.append(mes)
    # await bot.send(mes)
    # print(img_send)
    # await bot.send(img)
    mesg_a.append(saaImage(img))
    await MessageFactory(mesg_a).send()


@who_is.got("arg")
async def _(
    matcher: Matcher,
    ev: Event,
    state: T_State,
    resp: str = ArgPlainText(),
):
    name: str = state["name"]
    try:
        async with timeout(ONE_TURN_TIME):
            while True:
                if resp is not None:
                    s = resp.text.strip()
                    gid = resp.group_id
                    uid = resp.user_id
                    cid = roster.get_id(s)
                    # await bot.send(f'你说的是 {resp.text} 吧？')
                    if (
                        cid != 9999
                        and cid
                        == winner_judger.get_correct_chara_id(ev.get_session_id())
                        and winner_judger.get_winner(ev.get_session_id()) == ""
                    ):
                        GAME = GAME_DB()
                        win_num = GAME.update_game_num(uid, "whois")
                        mesg_d = []
                        mesg = ""
                        if daily_whois_limiter.check(uid):
                            SCORE = SCORE_DB()
                            SCORE.update_score(uid, 1000)
                            daily_whois_limiter.increase(uid)
                            mesg = "获得1000金币\n"
                        winner_judger.record_winner(ev.get_session_id(), ev.user_id)
                        win_mes = winner_judger.get_correct_win_pic(gid)
                        winner_judger.turn_off(ev.get_session_id())
                        POKE = PokeCounter()
                        mapinfo = POKE._get_map_now(uid)
                        myname = mapinfo[2]
                        myname = str(myname)[:10]
                        mes = f"{myname}猜对了，真厉害！\n{mesg}TA已经猜对{win_num}次了\n正确答案是:{name}"
                        chongsheng_num = await POKE.get_chongsheng_num(uid, 150)

                        await POKE.update_chongsheng(uid, 150, 1)
                        mesg_d.append(mes)
                        mesg_d.append(saaImage(win_mes))
                        await MessageFactory(mesg_d).send()
                        return
    except asyncio.TimeoutError:
        pass
    if winner_judger.get_winner(ev.get_session_id()) != "":
        winner_judger.turn_off(ev.get_session_id())
        return
    winner_judger.turn_off(ev.get_session_id())
    mes = f"很遗憾，没有人答对~\n正确答案是:{name}"
    mesg_c = []
    mesg_c.append(mes)
    mesg_c.append(saaImage(win_mes))
    await MessageFactory(mesg_c).send()


re_who_is = on_command("重置我是谁", aliases={"rewho"}, priority=5, block=True)


@re_who_is.handle("")
async def cz_pokemon_whois(matcher: Matcher, ev: Event):
    winner_judger.turn_off(ev.get_session_id())
    await matcher.send("重置成功，请重新发送我是谁开始新一轮游戏")


async def convert_img(im: Image.Image) -> io.BytesIO:
    image_data = io.BytesIO()
    im.save(image_data, format="JPEG")
    return image_data
