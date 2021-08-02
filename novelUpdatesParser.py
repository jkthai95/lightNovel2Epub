from bs4 import BeautifulSoup
from urllib.parse import urlparse, urlsplit
import os
import utils
from hostedNovelParser import hostedNovelParser
from ebooklib import epub

chapterParserMap = {
    "hostednovel": hostedNovelParser()
}


class novelUpdatesParser:
    def __init__(self, url=None, downloadPathBase="data"):
        self.url = url
        self.seriesTitle = None
        self.downloadPathBase = downloadPathBase
        self.downloadPathSeries = None
        self.epub = None
        self.epubOld = None
        self.chapters = []
        self.bookPath = None

        if url:
            self.parseURL()

    def updateURL(self, url):
        if url != self.url:
            self.__init__(url)

    def parseURL(self):
        table = None
        while table is None:
            html = utils.getHtml(self.url)
            soup = BeautifulSoup(html, 'html.parser')
            table = soup.find('table', id='myTable')
            if table:
                if self.seriesTitle is None:
                    self.seriesTitle = soup.find('div', {'class': 'seriestitlenu'}).contents[0]
                    self.downloadPathSeries = os.path.join(self.downloadPathBase, self.seriesTitle)
                    if not os.path.exists(self.downloadPathSeries):
                        os.makedirs(self.downloadPathSeries)
                    self.bookPath = os.path.join(self.downloadPathSeries, "{}.epub".format(self.seriesTitle))
                    if os.path.exists(self.bookPath):
                        renameIdx = 0
                        renamePath = os.path.join(self.downloadPathSeries, "{} - Old {}.epub".format(self.seriesTitle, renameIdx))
                        while os.path.exists(renamePath):
                            renameIdx = renameIdx + 1
                            renamePath = os.path.join(self.downloadPathSeries, "{} - Old {}.epub".format(self.seriesTitle, renameIdx))
                        self.epubOld = epub.read_epub(self.bookPath)
                        os.rename(self.bookPath, renamePath)
                    self.epub = epub.EpubBook()
                    self.epub.set_identifier(self.seriesTitle)
                    self.epub.set_title(self.seriesTitle)
                    self.epub.set_language('en')
                    print("Series Title:", self.seriesTitle)
                self.parseTable(table)
        self.createBook()

    def parseTable(self, table):
        tableBody = table.find('tbody')
        rows = tableBody.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            chapterData = cols[-1]
            chapterLinks = chapterData.find_all('a', href=True)
            for chapterLink in chapterLinks:
                chapter = chapterLink['title']
                print(chapter)
                chapterPath = "{}.xhtml".format(chapter)
                if self.epubOld and self.epubOld.get_item_with_href(chapterPath):
                    print("skipping")
                    self.copyChapter(chapter, self.epubOld.get_item_with_href(chapterPath).get_content())
                    break
                else:
                    href = urlparse(chapterLink['href'], 'https').geturl()
                    self.downloadChapter(chapter, href)

    def createBook(self):
        self.epub.toc = tuple(self.chapters)

        style = 'BODY {color: white}'
        navCSS = epub.EpubItem(uid='style_nav', file_name='style/nav.css', media_type='text/css', content=style)
        self.epub.add_item(navCSS)
        self.epub.add_item(epub.EpubNcx())
        self.epub.add_item(epub.EpubNav())

        self.epub.spine = self.chapters

        epub.write_epub(self.bookPath, self.epub, {})

    def downloadChapter(self, chapter, url):
        downloadPathChapter = os.path.join(self.downloadPathSeries, chapter)

        if os.path.exists(downloadPathChapter):
            return

        canonicalLink = None
        baseSite = None
        html = ""
        while canonicalLink is None:
            html = utils.getHtml(url)
            soup = BeautifulSoup(html, 'html.parser')
            canonicalLinks = soup.find_all('link', {'rel': 'canonical'}, href=True)
            if len(canonicalLinks):
                canonicalLink = canonicalLinks[0]['href']
                splitLink = urlsplit(canonicalLink)
                baseSite = splitLink.netloc.split(".")[-2].lower()

        if baseSite in chapterParserMap:
            chapterParserMap[baseSite].parse(soup)
        else:
            return

        self.addChapter(chapter, chapterParserMap[baseSite].text)

    def copyChapter(self, chapter, html):
        self.addChapter(chapter, html)

    def addChapter(self, chapter, html):
        chapterPath = "{}.xhtml".format(chapter)
        chapterItem = epub.EpubHtml(title=chapter, file_name=chapterPath, lang='en')
        chapterItem.set_content(html)
        self.epub.add_item(chapterItem)
        self.chapters.insert(0, chapterItem)    # assumes chapters are inserted in reverse order

