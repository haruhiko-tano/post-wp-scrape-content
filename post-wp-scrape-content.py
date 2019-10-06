# coding: UTF-8
import urllib.request, urllib.error
from bs4 import BeautifulSoup
from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods.posts import GetPosts, NewPost
from wordpress_xmlrpc.methods.users import GetUserInfo
from datetime import datetime
from wordpress_xmlrpc.methods import media
import random
import os


wp = Client('[input your prameter]', os.environ['WORDPRESS_USER'],os.environ['WORDPRESS_PASS'])
dmmURL = "https://api.dmm.com/affiliate/v3/ItemList?api_id=" + os.environ['DMM_API_ID'] + "&affiliate_id=" + os.environ['DMM_AFFILIATE_ID'];
excludeTag = "[input your prameter]"

headers = {
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:47.0) Gecko/20100101 Firefox/47.0",
}

class ScrapedContent:
    def __init__(self,id, title, imgTag, movieUrl,category,tags):
        self.id = id
        self.title = title
        self.imgTag = imgTag
        self.movieUrl = movieUrl
        self.category = category
        self.tags = tags


def fetchExistedTitles():
    titles = [];
    posts = wp.call(GetPosts({'number': 1000}))
    for post in posts:
        titles.append(str(post.title))

    return titles;

def scrapeArticle(url):
    # URLにアクセスする htmlが帰ってくる → <html><head><title>経済、株価、ビジネス、政治のニュース:日経電子版</title></head><body....
    request = urllib.request.Request(url=url,headers=headers)
    html = urllib.request.urlopen(request)
    # htmlをBeautifulSoupで扱う
    soup = BeautifulSoup(html, "html.parser")
    article = soup.find_all("article")

    items = [];
    for tag in article:

        detailUrl = "[input your prameter]" + tag.find("a").get("href")
        detailRequest = urllib.request.Request(url=detailUrl,headers=headers)
        detailHtml = urllib.request.urlopen(detailRequest)
        detailSoup = BeautifulSoup(detailHtml, "html.parser")

        scrapedtags = detailSoup.select("div.video_category_list")
        isExcludeContent = False
        tagList = [];
        for tag in scrapedtags:
            tagList.append(str(tag.string));
            if excludeTag in tag.string:
                isExcludeContent = True
        if isExcludeContent:
            continue

        category = "";
        resultTagList = [];
        for tagItem in tagList:
            if isActorForDMM(tagItem):
                if category == "":
                    category = tagItem
            else:
                resultTagList.append(tagItem)

        items.append(ScrapedContent(str(tag.get("id")),str(detailSoup.select_one("h1.entry-title").string),detailSoup.find("img").get("src"),str(detailSoup.find("iframe")),category,resultTagList))
    return items

def getMediaId(item):
    fetchImgReq = urllib.request.Request(url=item.imgTag,headers=headers)
    r = urllib.request.urlopen(fetchImgReq).read()
    data = {
    "name": item.id+".jpeg",
    "type": 'image/jpeg',
    "overwrite": True,
    "bits": r
    }
    mediaId = wp.call(media.UploadFile(data))['id']
    return mediaId


def postWordpress(item):

    post = WordPressPost()
    post.title = item.title
    post.content = item.movieUrl
    if item.category == "":
        post.terms_names = {
            'post_tag': item.tags
        }
    else:
        category = []
        category.append(item.category)
        post.terms_names = {
            'post_tag': item.tags,
            'category': category
        }
    post.slug = '[input your prameter]'

    # 投稿時間
    # 現在時間で投稿
    post.date = datetime.now()
    # 予約投稿の場合（例：2017年2月2日0時0分0秒0マイクロ秒）
    #month = random.randint(1,10)
    #day = random.randint(1,22)
    #post.date = datetime(2018, month, day, 0, 0, 0, 0)

    # 投稿する。
    # ステータスを公開済にする。
    post.post_status = 'publish'
    # これなら下書き指定
    # post.post_status = 'draft'

    post.thumbnail = getMediaId(item)
    wp.call(NewPost(post))


def isActorForDMM(keyword: str):
    url = dmmURL + "&site=FANZA&service=digital&floor=videoa&hits=10&sort=date&keyword="+ urllib.parse.quote_plus(keyword, encoding='utf-8') + "&output=xml";
    html = urllib.request.urlopen(url)
    soup = BeautifulSoup(html,"html.parser")

    items = soup.items #1つ1つのitemオブジェクトを取得
    for item in items:
        actress = item.actress
        if actress is not None:
            for actor in actress:
                if keyword ==actor.find("name").string:
                    return True;
    print(keyword + "is not actor!")
    return False;

def main(self):
    existedTitles = fetchExistedTitles();
    for i in range(2, 5):
        url = "[input your prameter]"+"/page/"+str(i)
        items = scrapeArticle(url)
        for item in items:
            print(item.title)
            if item.title in existedTitles:
                print("existed!")
                continue
            postWordpress(item)
