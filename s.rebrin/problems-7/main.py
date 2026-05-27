from __future__ import annotations

import re
import time
from typing import Dict, Union, MutableMapping

import requests
from bs4 import BeautifulSoup


BASE = "https://en.wikipedia.org"


def strip_parentheses(html: str) -> str:
    return re.sub(r"\([^()]*\)", "", html)


def extract_title(url: str) -> str:
    return url.split("/wiki/")[-1].replace("_", " ")


def is_philosophy(url: str) -> bool:
    return extract_title(url).lower() == "philosophy"


def find_first_link(html: str) -> str | None:
    html = strip_parentheses(html)
    soup = BeautifulSoup(html, "html.parser")

    content = soup.find(id="mw-content-text")
    if not content:
        return None

    for p in content.find_all("p"):
        if not p.text.strip():
            continue

        for a in p.find_all("a", href=True):
            href = a.get("href")
            if not isinstance(href, str):
                continue

            if not href.startswith("/wiki/"):
                continue

            if any(
                x in href
                for x in (
                    "Special",
                    "Help",
                    "File",
                    "Category",
                    "Portal",
                    "Wikipedia",
                    "Main_Page",
                )
            ):
                continue

            return BASE + href

    return None


def get_random_page() -> str:
    url = "https://en.wikipedia.org/w/api.php"

    params: Dict[str, Union[str, int]] = {
        "action": "query",
        "format": "json",
        "list": "random",
        "rnnamespace": 0,
        "rnlimit": 1,
    }

    headers: MutableMapping[str, str | bytes] = {
        "User-Agent": "NSU-Python-Course/1.0 (student project)"
    }

    r = requests.get(url, params=params, headers=headers)
    print(r.status_code)
    print(r.headers.get("Content-Type"))
    print(r.text[:500])
    data = r.json()

    title = data["query"]["random"][0]["title"]
    return f"{BASE}/wiki/{title.replace(' ', '_')}"


class WikiIterator:
    headers: MutableMapping[str, str | bytes] = {
        "User-Agent": "NSU-Python-Course/1.0 (student project)"
    }

    def __init__(self, start_url: str, sleep_time: float = 0.5, max_steps: int = 50):
        self.current: str | None = start_url
        self.visited: set[str] = set()
        self.sleep = sleep_time
        self.steps = 0
        self.max_steps = max_steps

    def __iter__(self) -> WikiIterator:
        return self

    def __next__(self) -> str:
        if self.current is None:
            raise StopIteration
        if self.current in self.visited:
            print(self.current, "- cycle")
            raise StopIteration

        if is_philosophy(self.current):
            print(self.current, "- reached philosophy")
            raise StopIteration

        if self.steps >= self.max_steps:
            print("Too deep")
            raise StopIteration

        self.visited.add(self.current)
        self.steps += 1

        result = self.current

        resp = requests.get(self.current, headers=self.headers)
        if resp.status_code != 200:
            print("HTTP error:", resp.status_code)
            raise StopIteration

        next_link = find_first_link(resp.text)

        if not next_link:
            print(self.current, "- no valid link")
            self.current = None
            return result

        self.current = next_link
        time.sleep(self.sleep)

        return result


def main() -> None:
    start = get_random_page()
    print("Start:", start)

    for page in WikiIterator(start):
        print(page)
        cmd = input("> ")
        if cmd in ("e", "exit"):
            break


if __name__ == "__main__":
    main()
