#coding=utf-8
import json, re
from urllib.parse import quote
from base.spider import Spider

class Spider(Spider):
    def getName(self): return '漫蛙动漫'
    def init(self, extend=""): pass
    def isVideoFormat(self, url): return False
    def manualVideoCheck(self): return False

    def __init__(self):
        self.h = 'https://www.mwdm.cc'
        self.header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', 'Referer': self.h}

    def homeContent(self, filter):
        return {'class': [{'type_id': '2', 'type_name': '国漫'}, {'type_id': '3', 'type_name': '日漫'}, {'type_id': '1', 'type_name': '番漫'}, {'type_id': '4', 'type_name': '其他'}]}

    def homeVideoContent(self): return self._list(self.h)
    def categoryContent(self, tid, pg, filter, extend): return self._list(f'{self.h}/list/{tid}-{pg}/', pg)

    def searchContent(self, key, quick, pg=1): 
        return self._list(f"{self.h}/search/-------------/?wd={quote(key)}&page={pg}", pg)

    def detailContent(self, ids):
        try:
            t = self.fetch(f'{self.h}/manwa/{ids[0]}/', headers=self.header).text
            tit = re.search(r'title">([^<]+)</h3>', t).group(1)
            pic = re.search(r'thumb">.*?src="([^"]+)"', t, re.S).group(1)
            desc = re.search(r'description" content="([^"]+)"', t).group(1)
            tabs = re.findall(r'href="#(down\d+-\d+)"[^>]*>([^<]+)</a>', t)
            p_f, p_u = [], []
            for tid, nm in tabs:
                p_f.append(nm)
                it = re.findall(r'href="([^"]+)">([^<]+)</a>', re.search(f'id="{tid}"(.*?)</ul>', t, re.S).group(1))
                p_u.append("#".join([f"{n}${l}" for l, n in it]))
            return {'list': [{'vod_id': ids[0], 'vod_name': tit, 'vod_pic': pic if pic.startswith('http') else self.h+pic, 'vod_content': desc, 'vod_play_from': "$$$".join(p_f), 'vod_play_url': "$$$".join(p_u)}]}
        except: return {'list': []}

    def playerContent(self, flag, id, vipFlags):
        try:
            t = self.fetch(f'{self.h}{id}', headers=self.header).text
            u = json.loads(re.search(r'player_aaaa=(.*?);', t).group(1))['url']
            return {'parse': 0, 'url': u, 'header': self.header}
        except: return {'parse': 1, 'url': f'{self.h}{id}'}

    def _list(self, url, pg=1):
        try:
            t = self.fetch(url, headers=self.header).text
            v = []
            for h, p, r, tit in re.findall(r'thumb lazyload.*?href="([^"]+)".*?original="([^"]+)".*?text-right">([^<]+)</span>.*?title="([^"]+)"', t, re.S):
                vid = re.search(r'/manwa/(\d+)/', h).group(1) if '/manwa/' in h else h
                v.append({'vod_id': vid, 'vod_name': tit, 'vod_pic': p if p.startswith('http') else self.h+p, 'vod_remarks': r.strip()})
            return {'list': v, 'page': pg}
        except: return {'list': []}
