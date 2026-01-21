import sys, urllib.parse
from base.spider import Spider

class Spider(Spider):
    def __init__(self):
        self.name = 'KanAV'
        self.host = 'https://kanav.ad'
        self.headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}

    def getName(self): return self.name
    def init(self, extend=""): pass

    def homeContent(self, filter):
        types = ['中文字幕','日韩有码','日韩无码','国产AV','自拍泄密','探花约炮','主播录制','里番','泡面番','Anime','3D动画','同人作品']
        ids = ['1','2','3','4','30','31','32','25','26','27','28','29']
        return {'class': [{'type_id': i, 'type_name': n} for i, n in zip(ids, types)]}

    def homeVideoContent(self):
        return {'list': self._parse_video_list(self.fetch(self.host, headers=self.headers).text)}

    def categoryContent(self, tid, pg, filter, extend):
        url = f'{self.host}/index.php/vod/type/id/{tid}/page/{pg}.html'
        return {'list': self._parse_video_list(self.fetch(url, headers=self.headers).text), 'page': pg, 'pagecount': 999}

    def detailContent(self, ids):
        v_id = ids[0]
        doc = self.html(self.fetch(f'{self.host}/index.php/vod/play/id/{v_id}/sid/1/nid/1.html', headers=self.headers).text)
        pic = doc.xpath('//meta[@property="og:image"]/@content')
        return {'list': [{
            'vod_id': v_id,
            'vod_name': doc.xpath('//title/text()')[0].split('-')[1].strip(),
            'vod_pic': pic[0] if pic else "",
            'vod_play_from': 'KanAV',
            'vod_play_url': f"立即播放${v_id}"
        }]}

    def searchContent(self, key, quick, pg="1"):
        url = f'{self.host}/index.php/vod/search/page/{pg}/wd/{urllib.parse.quote(key)}.html'
        return {'list': self._parse_video_list(self.fetch(url, headers=self.headers).text)}

    def playerContent(self, flag, id, vipFlags):
        return {'parse': 1, 'url': f'{self.host}/index.php/vod/play/id/{id}/sid/1/nid/1.html', 'header': self.headers}

    def _parse_video_list(self, html_str):
        videos = []
        for item in self.html(html_str).xpath('//div[contains(@class, "video-item")]'):
            try:
                link = item.xpath('.//a/@href')[0]
                remark = item.xpath('.//span[@class="model-view"]/text()')
                videos.append({
                    'vod_id': link.split('/id/')[1].split('/')[0].replace('.html', ''),
                    'vod_name': item.xpath('.//img/@alt')[0],
                    'vod_pic': item.xpath('.//img/@src')[0],
                    'vod_remarks': remark[0] if remark else ""
                })
            except: continue
        return videos
