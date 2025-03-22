import asyncio
import aiohttp
import aiomysql
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from time import time

## Morao mrtvi object oriented class da uvedem smrt OOP-u
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
                    target_element = soup.find(self.html_element, class_=self.class_id)
                    return soup, target_element.get_text(strip=True) if target_element else None
                return None, None
        except Exception as e:
            print(f"Error fetching {url}: {str(e)}")
            return None, None

    async def find_links(self, soup, base_url):
        if not soup:
            return
        for link in soup.find_all('a'):
            href = link.get('href')
            if href:
                full_url = urljoin(base_url, href)
                ## Lock mi jos uvek nije jasan al sam skontao da mora da se stavi (ovo je delo DeepSeek-a)
                async with self.lock:
                    if full_url not in self.discovered_urls:
                        self.discovered_urls.add(full_url)
                        await self.url_queue.put(full_url)

    async def worker(self, session, pool):
        while True:
            try:
                url = await asyncio.wait_for(self.url_queue.get(), timeout=10)
                print(f"Processing: {url}")
                
                soup, content = await self.parse_html(url, session)
                if content:
                    async with pool.acquire() as conn:
                        async with conn.cursor() as cur:
                            await cur.execute(
                                
                                ## Pakao boziji nz kako cu da ucinim da moze da prima x broj column-a i da generise nove column-e kada ne postoje u MySQL, vrv cu se upucati tad
                                f"INSERT INTO scraped_links (url, {self.sql_column}) VALUES (%s, %s)",
                                (url, content)
                            )
                            await conn.commit()
                
                await self.find_links(soup, url)
                self.url_queue.task_done()
                
            except asyncio.TimeoutError:
                if self.url_queue.empty():
                    break

    async def run(self):
        start_time = time()
        
        await self.url_queue.put(self.start_url)
        self.discovered_urls.add(self.start_url)
        
        ## Pool mi je oduzeo dusu dok sam ga skontao kako se integrise
        db_pool = await aiomysql.create_pool(
            host='localhost',
            user='reggie',
            password='R^/LbeElxoC}ZnH+z~*|',
            db='crawler_db',
            minsize=5,
            maxsize=15
        )
        
        ## Workeri takodje, msm da sam samo random stavljao await na svaku komandu dok nisam istrebio sve await errore
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
