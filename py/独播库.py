import sys
import re
import json
import urllib.parse
from base.spider import Spider

class Spider(Spider):
    def __init__(self):
        self.name = '独播库'
        self.host = 'https://www.dbku.tv'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': self.host
        }
        self.video_cache = {}
        self.category_cache = {
            '4': '动漫', '20': '港剧', '13': '陆剧', '21': '短剧', '1': '电影','2': '连续剧', '3': '综艺', '14': '台泰剧', '15': '日韩剧'
        }

    def getName(self): return self.name
    def init(self, extend=""): pass
    def isVideoFormat(self, url): return False
    def manualVideoCheck(self): return False
    def destroy(self): pass
    def localProxy(self, param): return None

    def homeContent(self, filter):
        return {'class': [{'type_id': k, 'type_name': v} for k, v in self.category_cache.items()]}

    def homeVideoContent(self):
        try:
            rsp = self.fetch(self.host, headers=self.headers)
            return {'list': self._parse_video_list(rsp.text)[:20]}
        except: return {'list': []}

    def categoryContent(self, tid, pg, filter, extend):
        try:
            page_num = int(pg)
            url = f"{self.host}/vodtype/{tid}.html" if page_num == 1 else f"{self.host}/vodshow/{tid}--------{page_num}---.html"
            print(f"请求分类URL: {url}")
            rsp = self.fetch(url, headers=self.headers)
            videos = self._parse_video_list(rsp.text)
            pagecount = max(self._parse_pagecount(rsp.text, tid), 1)
            return {'list': videos, 'page': page_num, 'pagecount': pagecount, 'limit': 20, 'total': len(videos) * pagecount}
        except: return {'list': []}

    def detailContent(self, ids):
        try:
            vid = ids[0]
            url = self.video_cache.get(vid, {}).get('url', f"{self.host}/voddetail/{vid}.html")
            print(f"详情页URL: {url}")
            rsp = self.fetch(url, headers=self.headers)
            
            # 提取基本信息
            name = self._extract_detail(rsp.text, r'<h1[^>]*class="[^"]*title[^"]*"[^>]*>([^<]+)</h1>', vid, 'name')
            pic = self._extract_detail(rsp.text, r'<img[^>]*class="[^"]*lazyload[^"]*"[^>]*data-original="([^"]+)"', vid, 'pic')
            
            # 提取描述 - 修正正则表达式
            desc_patterns = [
                r'<div[^>]*class="[^"]*text-collapse[^"]*"[^>]*>.*?<span[^>]*class="[^"]*data[^"]*"[^>]*>.*?<p>([^<]+)</p>',
                r'<div[^>]*class="[^"]*col-pd[^"]*"[^>]*>.*?<span[^>]*class="[^"]*sketch[^"]*"[^>]*>([^<]+)</span>',
                r'<div[^>]*class="[^"]*content[^"]*"[^>]*>([^<]+)</div>'
            ]
            
            desc = ''
            for pattern in desc_patterns:
                desc_match = re.search(pattern, rsp.text, re.S)
                if desc_match:
                    desc = desc_match.group(1).strip()
                    break
            
            if not desc:
                # 尝试提取隐藏的描述内容
                hidden_desc = re.search(r'<span[^>]*class="[^"]*data[^"]*"[^>]*style="[^"]*display:\s*none[^"]*"[^>]*>(.*?)</span>', rsp.text, re.S)
                if hidden_desc:
                    # 移除HTML标签
                    desc = re.sub(r'<[^>]+>', '', hidden_desc.group(1)).strip()
            
            # 提取年份和地区
            year = self._extract_detail(rsp.text, r'<a[^>]*href="[^"]*-----------(\d{4})\.html"[^>]*>', default='')
            area = self._extract_detail(rsp.text, r'<a[^>]*href="[^"]*大陆----------\.html"[^>]*>([^<]+)</a>', default='大陆')
            
            # 提取演员
            actors = []
            actor_match = re.search(r'<span[^>]*class="[^"]*text-muted[^"]*"[^>]*>主演：</span>(.*?)</p>', rsp.text, re.S)
            if actor_match:
                actor_text = actor_match.group(1)
                actor_links = re.findall(r'<a[^>]*>([^<]+)</a>', actor_text)
                actors = actor_links
            
            # 提取导演
            director = ''
            director_match = re.search(r'<span[^>]*class="[^"]*text-muted[^"]*"[^>]*>导演：</span>.*?<a[^>]*>([^<]+)</a>', rsp.text, re.S)
            if director_match:
                director = director_match.group(1)
            
            # 提取播放列表 - 修正正则表达式
            play_url = []
            play_from = ['独播库']
            
            # 尝试匹配视频列表区域
            playlist_patterns = [
                r'<div[^>]*class="[^"]*myui-panel[^"]*"[^>]*>.*?视频列表.*?<ul[^>]*class="[^"]*myui-content__list[^"]*"[^>]*>(.*?)</ul>',
                r'<div[^>]*id="playlist[^"]*"[^>]*>.*?<ul[^>]*class="[^"]*myui-content__list[^"]*"[^>]*>(.*?)</ul>',
                r'<ul[^>]*class="[^"]*myui-content__list[^"]*"[^>]*>(.*?)</ul>'
            ]
            
            episodes = []
            for pattern in playlist_patterns:
                playlist_match = re.search(pattern, rsp.text, re.S)
                if playlist_match:
                    playlist_html = playlist_match.group(1)
                    # 提取每个剧集链接
                    episode_matches = re.findall(r'<a[^>]*href="([^"]*)"[^>]*>([^<]+)</a>', playlist_html)
                    if episode_matches:
                        episodes = episode_matches
                        break
            
            # 如果没有找到剧集，尝试默认剧集
            if not episodes:
                # 检查是否有默认播放按钮
                default_play = re.search(r'<a[^>]*class="[^"]*btn[^"]*"[^>]*href="([^"]*)"[^>]*>.*?立即播放', rsp.text, re.S)
                if default_play:
                    play_url = f"第1集${self._make_full_url(default_play.group(1))}"
                else:
                    # 生成默认剧集
                    for i in range(1, 7):
                        episodes.append((f"/vodplay/{vid}-1-{i}.html", f"第{i}集"))
            
            # 处理剧集列表
            if episodes:
                episode_list = []
                for url, title in episodes:
                    full_url = self._make_full_url(url)
                    episode_list.append(f"{title}${full_url}")
                play_url = '#'.join(episode_list)
            
            # 构建VOD对象
            vod = {
                'vod_id': vid,
                'vod_name': name,
                'vod_pic': pic,
                'vod_content': desc,
                'vod_year': year,
                'vod_area': area,
                'vod_remarks': f"{year} | {area}",
                'vod_play_from': '$$$'.join(play_from),
                'vod_play_url': play_url if isinstance(play_url, str) else '$$$'.join(play_url)
            }
            
            # 添加演员和导演信息
            if actors:
                vod['vod_actor'] = ' / '.join(actors)
            if director:
                vod['vod_director'] = director
            
            return {'list': [vod]}
        except Exception as e:
            print(f"详情页解析错误: {e}")
            import traceback
            traceback.print_exc()
            return {'list': []}

    def searchContent(self, key, quick, pg="1"):
        try:
            page_num, encoded_key = int(pg), urllib.parse.quote(key)
            url = f"{self.host}/vodsearch/{encoded_key}------------{page_num}---.html" if page_num > 1 else f"{self.host}/vodsearch/-------------.html?wd={encoded_key}"
            print(f"搜索URL: {url}")
            rsp = self.fetch(url, headers=self.headers)
            videos = self._parse_video_list(rsp.text) or self._parse_search_results(rsp.text)
            pagecount = max(self._parse_pagecount(rsp.text, 'search'), 1)
            return {'list': videos, 'page': page_num, 'pagecount': pagecount}
        except: return {'list': []}

    def playerContent(self, flag, id, vipFlags):
        try:
            if id.startswith('http'):
                play_url = id
            elif 'vodplay' in id:
                play_url = f"{self.host}{id}" if id.startswith('/') else f"{self.host}/{id}"
            else:
                rsp = self.fetch(f"{self.host}/vodplay/{id}.html", headers=self.headers)
                for pattern in [r'url\s*[:=]\s*["\']([^"\']+\.m3u8[^"\']*)["\']', r'src\s*[:=]\s*["\']([^"\']+\.m3u8[^"\']*)["\']', r'video_url\s*[:=]\s*["\']([^"\']+\.m3u8[^"\']*)["\']']:
                    if match := re.search(pattern, rsp.text):
                        play_url = match.group(1)
                        break
                else:
                    play_url = f"{self.host}/vodplay/{id}.html"
            
            return {'parse': 0 if play_url.endswith('.m3u8') else 1, 'url': play_url, 'header': self.headers}
        except: return {'parse': 0, 'url': ''}

    # 辅助方法
    def _parse_video_list(self, html):
        videos = []
        # 修正正则表达式，匹配更通用的视频列表结构
        patterns = [
            r'<a[^>]*class="[^"]*myui-vodlist__thumb[^"]*"[^>]*href="/voddetail/(\d+)\.html"[^>]*title="([^"]*)"[^>]*data-original="([^"]*)"',
            r'<a[^>]*href="/voddetail/(\d+)\.html"[^>]*title="([^"]*)"[^>]*data-original="([^"]*)"'
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, html, re.S):
                try:
                    vid, name, pic = match.group(1), match.group(2), match.group(3)
                    # 提取备注信息
                    remark_match = re.search(r'<span[^>]*class="[^"]*pic-text[^"]*"[^>]*>([^<]*)</span>', html[match.end():match.end()+200], re.S)
                    remark = remark_match.group(1).strip() if remark_match else ''
                    
                    self.video_cache[vid] = {'name': name, 'pic': pic, 'url': f'{self.host}/voddetail/{vid}.html'}
                    videos.append({'vod_id': vid, 'vod_name': name, 'vod_pic': pic, 'vod_remarks': remark})
                    if len(videos) >= 48: break
                except: continue
            if videos: break
        return videos

    def _parse_search_results(self, html):
        videos = []
        for pattern in [r'<li[^>]*class="[^"]*col-lg-[^"]*"[^>]*>.*?<a[^>]*href="/voddetail/(\d+)\.html"[^>]*title="([^"]*)"[^>]*>.*?<img[^>]*data-original="([^"]*)"[^>]*>.*?<span[^>]*class="[^"]*pic-text[^"]*"[^>]*>([^<]*)</span>',
                       r'href="/voddetail/(\d+)\.html"[^>]*title="([^"]*)"[^>]*>.*?data-original="([^"]*)"[^>]*>.*?<span[^>]*class="[^"]*pic-text[^"]*"[^>]*>([^<]*)</span>',
                       r'href="/voddetail/(\d+)\.html".*?title="([^"]*)"[^>]*>.*?data-original="([^"]*)".*?<span[^>]*class="[^"]*pic-text[^"]*"[^>]*>([^<]*)</span>']:
            for match in re.finditer(pattern, html, re.S):
                try:
                    vid, name, pic = match.group(1), match.group(2), match.group(3)
                    remark = match.group(4).strip() if len(match.groups()) > 3 else ''
                    self.video_cache[vid] = {'name': name, 'pic': pic, 'url': f'{self.host}/voddetail/{vid}.html'}
                    videos.append({'vod_id': vid, 'vod_name': name, 'vod_pic': pic, 'vod_remarks': remark})
                    if len(videos) >= 20: break
                except: continue
            if videos: break
        return videos

    def _parse_pagecount(self, html, tid):
        try:
            max_page = 1
            patterns = [r'href="[^"]*vodsearch[^"]*------------(\d+)---\.html"', r'href="[^"]*page=(\d+)[^"]*"'] if tid == 'search' else [r'href="/vodshow/\d+--------(\d+)---\.html"']
            for pattern in patterns:
                if pages := re.findall(pattern, html):
                    max_page = max(max_page, max(int(p) for p in pages))
            
            for pattern in [r'(\d+)/(\d+)</a>', r'共(\d+)页']:
                if match := re.search(pattern, html):
                    max_page = max(max_page, int(match.group(2) if match.lastindex >= 2 else match.group(1)))
            
            return max_page
        except: return 1

    def _extract_detail(self, html, pattern, vid=None, key=None, default=''):
        """提取详情页信息"""
        if match := re.search(pattern, html, re.S):
            return match.group(1).strip()
        elif vid and key:
            return self.video_cache.get(vid, {}).get(key, default)
        return default
    
    def _make_full_url(self, url):
        """将相对URL转换为完整URL"""
        if url.startswith('http'):
            return url
        elif url.startswith('/'):
            return f"{self.host}{url}"
        else:
            return f"{self.host}/{url}"
