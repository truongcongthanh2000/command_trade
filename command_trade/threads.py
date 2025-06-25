import json
import time
from typing import Dict

import jmespath
from parsel import Selector
from playwright.async_api import async_playwright
from nested_lookup import nested_lookup
from .logger import Logger
from .config import Config
from .notification import Message
from datetime import datetime
import pytz
import subprocess
import sys
import re

def remove_redundant_spaces(text: str):
    lines = text.split('\n')
    cleaned_lines = []

    for line in lines:
        # Check if it's a progress line
        if re.match(r'^\|\s*.*?\s*\|.*$', line):
            if '100%' in line:
                # Keep the 100% progress line, but remove redundant spaces
                line = re.sub(r'\|\s*', '|', line)  # Remove spaces after first |
                line = re.sub(r'\s*\|', '|', line)  # Remove spaces before second |
                cleaned_lines.append(line)
            else:
                # Skip all other progress lines (0%-90%)
                continue
        else:
            cleaned_lines.append(line)

    return '\n'.join(cleaned_lines)
class Threads:
    """
    A basic interface for interacting with Threads.
    """
    BASE_URL = "https://www.threads.net"
    def __init__(self, config: Config, logger: Logger):
        self.config = config
        self.logger = logger
        self.map_last_timestamp = {}

        command = [sys.executable, "-m", "playwright", "install", "chromium"]
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            self.logger.error(Message(title=f"Error installing Playwright - Time: {datetime.fromtimestamp(int(time.time()), tz=pytz.timezone('Asia/Ho_Chi_Minh'))}", body=f"{stderr.decode('utf-8')}", chat_id=self.config.TELEGRAM_LOG_PEER_ID), True)
        else:
            msg = stdout.decode('utf-8') or 'Successful'
            msg = msg.replace('\u25a0', '')
            msg = remove_redundant_spaces(msg)
            self.logger.info(Message(title=f"Playwright installation successful - Time: {datetime.fromtimestamp(int(time.time()), tz=pytz.timezone('Asia/Ho_Chi_Minh'))}", body=msg, chat_id=self.config.TELEGRAM_LOG_PEER_ID), False)
    
    # Note: we'll also be using parse_thread function we wrote earlier:

    def parse_thread(self, data: Dict) -> Dict:
        """Parse Twitter tweet JSON dataset for the most important fields"""
        result = jmespath.search(
            """{
            text: post.caption.text,
            published_on: post.taken_at,
            id: post.id,
            pk: post.pk,
            code: post.code,
            username: post.user.username,
            user_pic: post.user.profile_pic_url,
            user_verified: post.user.is_verified,
            user_pk: post.user.pk,
            user_id: post.user.id,
            has_audio: post.has_audio,
            reply_count: view_replies_cta_string,
            like_count: post.like_count,
            images: post.image_versions2.candidates[0].url,
            image_count: post.carousel_media_count,
            videos: post.video_versions[].url
        }""",
            data,
        )
        result["videos"] = list(set(result["videos"] or []))
        if result["reply_count"] and type(result["reply_count"]) != int:
            result["reply_count"] = int(result["reply_count"].split(" ")[0])
        result[
            "url"
        ] = f"{self.BASE_URL}/@{result['username']}/post/{result['code']}"
        return result

    async def scrape_thread(self, url: str) -> dict:
        """Scrape Threads post and replies from a given URL"""
        try:
            async with async_playwright() as pw:
                # start Playwright browser
                browser = await pw.chromium.launch()
                context = await browser.new_context(viewport={"width": 1920, "height": 1080})
                page = await context.new_page()

                # go to url and wait for the page to load
                await page.goto(url)
                # wait for page to finish loading
                await page.wait_for_selector("[data-pressable-container=true]")
                # find all hidden datasets
                selector = Selector(await page.content())
                hidden_datasets = selector.css('script[type="application/json"][data-sjs]::text').getall()
                # find datasets that contain threads data
                for hidden_dataset in hidden_datasets:
                    # skip loading datasets that clearly don't contain threads data
                    if '"ScheduledServerJS"' not in hidden_dataset:
                        continue
                    if "thread_items" not in hidden_dataset:
                        continue
                    data = json.loads(hidden_dataset)
                    # datasets are heavily nested, use nested_lookup to find 
                    # the thread_items key for thread data
                    thread_items = nested_lookup("thread_items", data)
                    if not thread_items:
                        continue
                    # use our jmespath parser to reduce the dataset to the most important fields
                    threads = [self.parse_thread(t) for thread in thread_items for t in thread]
                    return {
                        # the first parsed thread is the main post:
                        "thread": threads[0],
                        # other threads are replies:
                        "replies": threads[1:],
                    }
            raise ValueError("could not find thread data in page")
        except Exception as err:
            self.logger.error(Message(
                title=f"Error Threads.scrape_thread - url={url}",
                body=f"Error: {err=}", 
                format=None,
                chat_id=self.config.TELEGRAM_LOG_PEER_ID
            ), True)
            return {}