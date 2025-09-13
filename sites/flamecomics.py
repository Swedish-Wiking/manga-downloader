import requests
import json
from bs4 import BeautifulSoup as bs
import re
import iso639
from .provider import Provider

CDN_URL = "https://cdn.flamecomics.xyz"
IMAGE_URL = CDN_URL + "/uploads/images/series/{id}/{token}/{file}"
INFO_URL = "https://flamecomics.xyz/series/{id}"

class FlameComics(Provider):

    def __init__(self, session:requests.Session, url) -> None:
        self.s = session
        self.id = self.parse_url(url)

    def parse_url(self, url):
        parse = re.search(r"series\/(?P<id>\d+)", url)
        return parse.group("id") # type: ignore

    @staticmethod
    def parse_info(payload:dict) -> dict:
        return {
            "series": payload["series"].get("title"),
            "writer": payload["series"].get("author"),
            "penciller": payload["series"].get("artist"),
            "genre": payload["series"].get("tags"),
            "summary": bs(payload["series"].get("description"), "html.parser").get_text(),
            "languageISO": iso639.Language.from_name(payload["series"].get("language")).part1,
            "scanInformation": "Reaper_Scans & Flame Comics",
        }

    def generate_image_urls(self, raw_images:dict[str,dict], token:str) -> list[str]:
        images = list()
        for raw in raw_images.values():
            images.append(
                IMAGE_URL.format(id = self.id, token = token, file = raw.get("name"))
            )
        return images[1:]

    def parse_chapters(self, payload:list[dict]) -> list[dict]:
        chapters = list()
        for c in payload:
            nbr = int(float(c.get("chapter", 0.0)))
            title = c.get("title")
            if not title:
                title = f"Chapter {nbr}"
            images = self.generate_image_urls(c.get("images"), c.get("token")) # type: ignore

            data = {
                "nr": nbr,
                "title": title,
                "images": images
            }

            chapters.append(data)

        return chapters

    def get_info(self) -> tuple[dict, list]:
        r = self.s.get(INFO_URL.format(id = self.id))
        series_page = bs(r.content, "html.parser")
        payload = json.loads(
            series_page.find(
                "script", 
                attrs = {"id": "__NEXT_DATA__"}
            ).text # type: ignore
        ).get("props").get("pageProps") 
        
        info = self.parse_info(payload)
        chapters = self.parse_chapters(payload["chapters"])
        return info, chapters

    def get_mediainfo(self) -> tuple[dict, list]:
        return self.get_info()

    def get_url(self) -> str:
        return INFO_URL.format(id = self.id)

    @staticmethod
    def domain() -> str:
        return "flamecomics.xyz"


