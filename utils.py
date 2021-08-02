import cloudscraper


def getHtml(url):
    scraper = cloudscraper.create_scraper()
    urlGet = scraper.get(url)
    return urlGet.content
