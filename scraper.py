import asyncio
import aiohttp
import aiomysql
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from time import time


class AsyncScraper:
    def __init__(self, start_url, sql_column, html_element, class_id):
        self.start_url = start_url
        self.sql_column = sql_column
        self.html_element = html_element
        self.class_id = class_id
        self.url_queue = asyncio.Queue()
        self.discovered_urls = set()
        self.lock = asyncio.Lock()
        
    async def parse_html(self, url, session):
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    search_args = {}
                    if self.class_id:
                        search_args['class_'] = self.class_id.strip()

                    target_element = soup.find(self.html_element, **search_args)
                    content = target_element.get_text(strip=True) if target_element else None
                    
                    await self.find_links(soup, url)
                    return content
                
        except Exception as e:
            print(f"Error fetching {url}: {str(e)}")
        return None

    async def find_links(self, soup, base_url):
        if not soup:
            return
        
        for link in soup.find_all('a'):
            href = link.get('href')
            if href:
                full_url = urljoin(base_url, href)
                parsed = urlparse(full_url)
                cleaned_url = parsed._replace(query="", fragment="").geturl()
                cleaned_url = cleaned_url.rstrip('/')

                async with self.lock:
                    if cleaned_url not in self.discovered_urls and self.start_url in cleaned_url:
                        self.discovered_urls.add(cleaned_url)
                        await self.url_queue.put(cleaned_url)

    async def worker(self, session, pool):
        while True:
            url = await self.url_queue.get()
            print(f"Processing: {url}")

            try:
                content = await self.parse_html(url, session)
                if content:
                    async with pool.acquire() as conn:
                        async with conn.cursor() as cur:
                            await cur.execute(
                                
                                f"INSERT INTO scraped_links (url, {self.sql_column}) VALUES (%s, %s)",
                                (url, content)
                            )
                            await conn.commit()
                
            except Exception as e:
                        print(f"Error processing {url}: {e}")

            finally:
                self.url_queue.task_done()
                print(f"Completed: {url} | Queue size: {self.url_queue.qsize()}") 

    async def run(self):
        start_time = time()

        self.url_queue = asyncio.Queue()
        
        await self.url_queue.put(self.start_url)
        self.discovered_urls.add(self.start_url)
        
        db_pool = await aiomysql.create_pool(
            host='localhost',
            user='reggie',
            password='R^/LbeElxoC}ZnH+z~*|',
            db='crawler_db',
            minsize=15,
            maxsize=30
        )
        
        async with aiohttp.ClientSession() as session:
            workers = [asyncio.create_task(self.worker(session, db_pool)) 
                      for _ in range(15)]
            
            await self.url_queue.join()
            
            for task in workers:
                task.cancel()
            await asyncio.gather(*workers, return_exceptions=True)
        
        db_pool.close()
        await db_pool.wait_closed()
        
        print(f"\nScraping completed in {time() - start_time:.2f} seconds")
        print(f"Total URLs processed: {len(self.discovered_urls)}")
