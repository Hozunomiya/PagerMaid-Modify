""" Pagermaid plugin base. """
import json, requests, re
from googletrans import Translator
from urllib.parse import urlparse
from pagermaid import bot, log
from pagermaid.listener import listener, config
from pagermaid.utils import clear_emojis, obtain_message
from telethon.tl.types import ChannelParticipantsAdmins
from os import remove


@listener(outgoing=True, command="guess",
          description="能不能好好说话？ - 拼音首字母缩写释义工具（需要回复一句话）")
async def guess(context):
    reply = await context.get_reply_message()
    await context.edit("获取中 . . .")
    if reply:
        pass
    else:
        context.edit("宁需要回复一句话")
        return True
    text = {'text': str(reply.message.replace("/guess ", "").replace(" ", ""))}
    guess_json = json.loads(
        requests.post("https://lab.magiconch.com/api/nbnhhsh/guess", data=text, verify=False).content.decode("utf-8"))
    guess_res = []
    if not len(guess_json) == 0:
        for num in range(0, len(guess_json)):
            guess_res1 = json.loads(json.dumps(guess_json[num]))
            guess_res1_name = guess_res1['name']
            try:
                guess_res1_ans = ", ".join(guess_res1['trans'])
            except:
                try:
                    guess_res1_ans = ", ".join(guess_res1['inputting'])
                except:
                    guess_res1_ans = "尚未录入"
            guess_res.extend(["词组：" + guess_res1_name + "\n释义：" + guess_res1_ans])
        await context.edit("\n\n".join(guess_res))
    else:
        await context.edit("没有匹配到拼音首字母缩写")


@listener(outgoing=True, command="admin",
          description="一键 AT 本群管理员（仅在群组中有效）")
async def admin(context):
    await context.edit('正在获取管理员列表中...')
    chat = await context.get_chat()
    try:
        admins = await context.client.get_participants(chat, filter=ChannelParticipantsAdmins)
    except:
        await context.edit('请在群组中运行。')
        return True
    admin_list = []
    for admin in admins:
        if admin.first_name is not None:
            admin_list.extend(['[' + admin.first_name + '](tg://user?id=' + str(admin.id) + ')'])
    await context.edit(' , '.join(admin_list))


@listener(outgoing=True, command="wiki",
          description="查询维基百科词条",
          parameters="<词组>")
async def wiki(context):
    translator = Translator()
    lang = config['application_language']
    await context.edit("获取中 . . .")
    try:
        message = await obtain_message(context)
    except ValueError:
        await context.edit("出错了呜呜呜 ~ 无效的参数。")
        return
    try:
        wiki_json = json.loads(requests.get("https://zh.wikipedia.org/w/api.php?action=query&list=search&format=json&formatversion=2&srsearch=" + message).content.decode(
                    "utf-8"))
    except:
        await context.edit("出错了呜呜呜 ~ 无法访问到维基百科。")
        return
    if not len(wiki_json['query']['search']) == 0:
        wiki_title = wiki_json['query']['search'][0]['title']
        wiki_content = wiki_json['query']['search'][0]['snippet'].replace('<span class=\"searchmatch\">', '**').replace('</span>', '**')
        wiki_time = wiki_json['query']['search'][0]['timestamp'].replace('T', ' ').replace('Z', ' ')
        try:
            await context.edit("正在生成翻译中 . . .")
            wiki_content = translator.translate(clear_emojis(wiki_content), dest=lang)
            message = '词条： [' + wiki_title + '](https://zh.wikipedia.org/zh-cn/' + wiki_title + ')\n\n' + wiki_content.text + '...\n\n此词条最后修订于 ' + wiki_time
        except ValueError:
            await context.edit("出错了呜呜呜 ~ 找不到目标语言，请更正配置文件中的错误。")
            return
        await context.edit(message)
    else:
        await context.edit("没有匹配到相关词条")


@listener(outgoing=True, command="ip",
          description="IPINFO （或者回复一句话）",
          parameters="<ip/域名>")
async def ipinfo(context):
    reply = await context.get_reply_message()
    await context.edit('正在查询中...')
    try:
        if reply:
            for num in range(0, len(reply.entities)):
                url = reply.message[reply.entities[num].offset:reply.entities[num].offset + reply.entities[num].length]
                url = urlparse(url)
                if url.hostname:
                    url = url.hostname
                else:
                    url = url.path
                ipinfo_json = json.loads(requests.get(
                    "http://ip-api.com/json/" + url + "?fields=status,message,country,regionName,city,lat,lon,isp,org,as,mobile,proxy,hosting,query").content.decode(
                    "utf-8"))
                if ipinfo_json['status'] == 'fail':
                    pass
                elif ipinfo_json['status'] == 'success':
                    ipinfo_list = []
                    ipinfo_list.extend(["查询目标： `" + url + "`"])
                    if ipinfo_json['query'] == url:
                        pass
                    else:
                        ipinfo_list.extend(["解析地址： `" + ipinfo_json['query'] + "`"])
                    ipinfo_list.extend(["地区： `" + ipinfo_json['country'] + ' - ' + ipinfo_json['regionName'] + ' - ' +
                                        ipinfo_json['city'] + "`"])
                    ipinfo_list.extend(["经纬度： `" + str(ipinfo_json['lat']) + ',' + str(ipinfo_json['lon']) + "`"])
                    ipinfo_list.extend(["ISP： `" + ipinfo_json['isp'] + "`"])
                    if not ipinfo_json['org'] == '':
                        ipinfo_list.extend(["组织： `" + ipinfo_json['org'] + "`"])
                    ipinfo_list.extend(
                        ['[' + ipinfo_json['as'] + '](https://bgp.he.net/' + ipinfo_json['as'].split()[0] + ')'])
                    if ipinfo_json['mobile']:
                        ipinfo_list.extend(['此 IP 可能为**蜂窝移动数据 IP**'])
                    if ipinfo_json['proxy']:
                        ipinfo_list.extend(['此 IP 可能为**代理 IP**'])
                    if ipinfo_json['hosting']:
                        ipinfo_list.extend(['此 IP 可能为**数据中心 IP**'])
                    await context.edit('\n'.join(ipinfo_list))
                    return True
        else:
            url = urlparse(context.arguments)
            if url.hostname:
                url = url.hostname
            else:
                url = url.path
            ipinfo_json = json.loads(requests.get(
                "http://ip-api.com/json/" + url + "?fields=status,message,country,regionName,city,lat,lon,isp,org,as,mobile,proxy,hosting,query").content.decode(
                "utf-8"))
            if ipinfo_json['status'] == 'fail':
                pass
            elif ipinfo_json['status'] == 'success':
                ipinfo_list = []
                if url == '':
                    ipinfo_list.extend(["查询目标： `本机地址`"])
                else:
                    ipinfo_list.extend(["查询目标： `" + url + "`"])
                if ipinfo_json['query'] == url:
                    pass
                else:
                    ipinfo_list.extend(["解析地址： `" + ipinfo_json['query'] + "`"])
                ipinfo_list.extend(["地区： `" + ipinfo_json['country'] + ' - ' + ipinfo_json['regionName'] + ' - ' +
                                    ipinfo_json['city'] + "`"])
                ipinfo_list.extend(["经纬度： `" + str(ipinfo_json['lat']) + ',' + str(ipinfo_json['lon']) + "`"])
                ipinfo_list.extend(["ISP： `" + ipinfo_json['isp'] + "`"])
                if not ipinfo_json['org'] == '':
                    ipinfo_list.extend(["组织： `" + ipinfo_json['org'] + "`"])
                ipinfo_list.extend(
                    ['[' + ipinfo_json['as'] + '](https://bgp.he.net/' + ipinfo_json['as'].split()[0] + ')'])
                if ipinfo_json['mobile']:
                    ipinfo_list.extend(['此 IP 可能为**蜂窝移动数据 IP**'])
                if ipinfo_json['proxy']:
                    ipinfo_list.extend(['此 IP 可能为**代理 IP**'])
                if ipinfo_json['hosting']:
                    ipinfo_list.extend(['此 IP 可能为**数据中心 IP**'])
                await context.edit('\n'.join(ipinfo_list))
                return True
        await context.edit('没有找到要查询的 ip/域名 ...')
    except:
        await context.edit('没有找到要查询的 ip/域名 ...')


@listener(outgoing=True, command="ipping",
          description="Ping （或者回复一句话）",
          parameters="<ip/域名>")
async def ipping(context):
    reply = await context.get_reply_message()
    await context.edit('正在查询中...')
    try:
        if reply:
            for num in range(0, len(reply.entities)):
                url = reply.message[reply.entities[num].offset:reply.entities[num].offset + reply.entities[num].length]
                url = urlparse(url)
                if url.hostname:
                    url = url.hostname
                else:
                    url = url.path
                pinginfo = requests.get(
                    "https://helloacm.com/api/ping/?cached&host=" + url).content.decode(
                    "utf-8")
                if pinginfo == 'null':
                    pass
                elif not pinginfo == 'null':
                    pinginfo = pinginfo.replace('"', '').replace("\/", '/').replace('\\n', '\n', 7).replace('\\n', '')
                    await context.edit(pinginfo)
                    return True
        else:
            url = urlparse(context.arguments)
            if url.hostname:
                url = url.hostname
            else:
                url = url.path
            if url == '':
                await context.edit('没有找到要查询的 ip/域名 ...')
                return True
            pinginfo = requests.get(
                "https://helloacm.com/api/ping/?cached&host=" + url).content.decode(
                "utf-8")
            if pinginfo == 'null':
                pass
            elif not pinginfo == 'null':
                pinginfo = pinginfo.replace('"', '').replace("\/", '/').replace('\\n', '\n', 7).replace('\\n', '')
                await context.edit(pinginfo)
                return True
        await context.edit('没有找到要查询的 ip/域名 ...')
    except:
        await context.edit('没有找到要查询的 ip/域名 ...')


@listener(outgoing=True, command="pixiv",
          description="查询插画信息（现仅支持第一张图）")
async def pixiv(context):
    reply = await context.get_reply_message()
    await context.edit('正在查询中...')
    try:
        if reply:
            for num in range(0, len(reply.entities)):
                url = reply.message[reply.entities[num].offset:reply.entities[num].offset + reply.entities[num].length]
                url = urlparse(url)
                try:
                    url = str(re.findall(r"\d+\.?\d*", url.path)[0])
                    pixiv_json = json.loads(requests.get(
                        "https://api.imjad.cn/pixiv/v2/?type=illust&id=" + url).content.decode(
                        "utf-8"))
                except:
                    await context.edit('呜呜呜出错了...可能是链接不上 API 服务器')
                try:
                    pixiv_tag = pixiv_json['error']['user_message']
                    await context.edit('没有找到要查询的 pixiv 作品...')
                    return True
                except:
                    pixiv_tag = []
                    if str(len(pixiv_json['illust']['meta_pages'])) == '0':
                        pixiv_num = str(
                            len(pixiv_json['illust']['meta_pages']) + 1)
                    else:
                        pixiv_num = str(
                            len(pixiv_json['illust']['meta_pages']))
                    pixiv_list = '[' + pixiv_json['illust']['title'] + '](https://www.pixiv.net/artworks/' + str(
                        pixiv_json['illust']['id']) + ')' + ' (1/' + pixiv_num + ')'
                    for nums in range(0, len(pixiv_json['illust']['tags'])):
                        pixiv_tag.extend(['#' + pixiv_json['illust']['tags'][nums]['name']])
                    try:
                        await context.edit('正在下载图片中 ...')
                        try:
                            r = requests.get('https://daidr.me/imageProxy/?url=' +
                                                    pixiv_json['illust']['meta_single_page']['original_image_url'])
                        except:
                            r = requests.get('https://daidr.me/imageProxy/?url=' +
                                             pixiv_json['illust']['meta_pages'][0]['image_urls']['original'])
                        with open("pixiv.jpg", "wb") as code:
                            code.write(r.content)
                        await context.edit('正在上传图片中 ...')
                        await context.client.send_file(context.chat_id, 'pixiv.jpg',
                                                       caption=pixiv_list + '\nTags: ' + ' , '.join(pixiv_tag),
                                                       reply_to=reply.id)
                        await context.delete()
                        remove('pixiv.jpg')
                    except:
                        pass
                    return True
        else:
            url = urlparse(context.arguments)
            try:
                url = str(re.findall(r"\d+\.?\d*", url.path)[0])
                pixiv_json = json.loads(requests.get(
                    "https://api.imjad.cn/pixiv/v2/?type=illust&id=" + url).content.decode(
                    "utf-8"))
            except:
                await context.edit('呜呜呜出错了...可能是链接不上 API 服务器')
            try:
                pixiv_tag = pixiv_json['error']['user_message']
                await context.edit('没有找到要查询的 pixiv 作品...')
                return True
            except:
                pixiv_tag = []
                if str(len(pixiv_json['illust']['meta_pages'])) == '0':
                    pixiv_num = str(
                        len(pixiv_json['illust']['meta_pages']) + 1)
                else:
                    pixiv_num = str(
                        len(pixiv_json['illust']['meta_pages']))
                pixiv_list = '[' + pixiv_json['illust']['title'] + '](https://www.pixiv.net/artworks/' + str(
                    pixiv_json['illust']['id']) + ')' + ' (1/' + pixiv_num + ')'
                for nums in range(0, len(pixiv_json['illust']['tags'])):
                    pixiv_tag.extend(['#' + pixiv_json['illust']['tags'][nums]['name']])
                try:
                    await context.edit('正在下载图片中 ...')
                    try:
                        r = requests.get('https://daidr.me/imageProxy/?url=' +
                                         pixiv_json['illust']['meta_single_page']['original_image_url'])
                    except:
                        r = requests.get('https://daidr.me/imageProxy/?url=' +
                                         pixiv_json['illust']['meta_pages'][0]['image_urls']['original'])
                    with open("pixiv.jpg", "wb") as code:
                        code.write(r.content)
                    await context.edit('正在上传图片中 ...')
                    await context.client.send_file(context.chat_id, 'pixiv.jpg',
                                                   caption=pixiv_list + '\nTags: ' + ' , '.join(pixiv_tag))
                    await context.delete()
                    remove('pixiv.jpg')
                except:
                    pass
                return True
        await context.edit('没有找到要查询的 pixiv 作品 ...')
    except:
        await context.edit('没有找到要查询的 pixiv 作品 ...')