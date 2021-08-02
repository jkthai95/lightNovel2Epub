from bs4 import BeautifulSoup


class hostedNovelParser:
    def __init__(self):
        self.text = ""
        self.title = ""

    def parse(self, soup):
        self.title = soup.find('h1', {'class': 'text-center m-0'}).getText()
        chapter = soup.find('div', {'id': 'chapter'})
        pList = chapter.find_all('p')
        textList = []
        for p in pList:
            textList.append(str(p))
            # textList.append(p.getText())
        text = "\n".join(textList)
        self.text = "<h1>{}</h1>\n".format(self.title) + (text)

