import sys,urllib.parse,json,re
from base.spider import Spider
class Spider(Spider):
    def __init__(self):self.name='KanAV';self.host='https://kanav.ad';self.headers={'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
    def getName(self):return self.name
    def init(self,extend=""):pass
    def homeContent(self,filter):
        t=['中文字幕','日韩有码','日韩无码','国产AV','自拍泄密','探花约炮','主播录制','里番','泡面番','Anime','3D动画','同人作品']
        ids=['1','2','3','4','30','31','32','25','26','27','28','29']
        return {'class':[{'type_id':i,'type_name':n}for i,n in zip(ids,t)]}
    def homeVideoContent(self):return {'list':self._parse(self.fetch(self.host,headers=self.headers).text)}
    def categoryContent(self,tid,pg,filter,extend):return {'list':self._parse(self.fetch(f'{self.host}/index.php/vod/type/id/{tid}/page/{pg}.html',headers=self.headers).text),'page':pg,'pagecount':999}
    def detailContent(self,ids):
        bid=ids[0];d=self.html(self.fetch(f'{self.host}/index.php/vod/play/id/{bid}/sid/1/nid/1.html',headers=self.headers).text)
        t=d.xpath('//div[contains(@class, "video-box-ather")]/h3/text()');title=t[0].strip() if t else "Unknown"
        desc=d.xpath('//div[contains(@class, "video-title")]/h1/text()');desc=desc[0].strip() if desc else ""
        pic=d.xpath('//img[@class="countext-img"]/@src');pic=pic[0] if pic else ""
        act=d.xpath('//div[contains(@class, "hr-actor")]/following-sibling::a/text()');actor=",".join(act) if act else ""
        return {'list':[{'vod_id':bid,'vod_name':title,'vod_pic':pic,'vod_actor':actor,'vod_content':desc,'vod_play_from':'KanAV','vod_play_url':f"立即播放${bid}"}]}
    def searchContent(self,key,quick,pg="1"):return {'list':self._parse(self.fetch(f'{self.host}/index.php/vod/search/page/{pg}/wd/{urllib.parse.quote(key)}.html',headers=self.headers).text)}
    def playerContent(self,flag,id,vipFlags):
        u=f'{self.host}/index.php/vod/play/id/{id}/sid/1/nid/1.html';h=self.fetch(u,headers=self.headers).text;m=re.search(r'var player_aaaa=({.*?})',h)
        if m:
            try:
                d=json.loads(m.group(1));pu=urllib.parse.unquote(d.get('url','').replace("JT","%"))
                return {'parse':0,'playUrl':'','url':pu,'header':self.headers}
            except:pass
        return {'parse':1,'url':u,'header':self.headers}
    def _parse(self,h):
        v=[];x=self.html(h).xpath
        for i in x('//div[contains(@class, "video-item")]'):
            try:
                l=i.xpath('.//a/@href')[0];r=i.xpath('.//span[@class="model-view"]/text()');p=i.xpath('.//img/@data-original') or i.xpath('.//img/@src')
                v.append({'vod_id':l.split('/id/')[1].split('/')[0].replace('.html',''),'vod_name':i.xpath('.//img/@alt')[0],'vod_pic':p[0] if p else "",'vod_remarks':r[0] if r else ""})
            except:continue
        return v
