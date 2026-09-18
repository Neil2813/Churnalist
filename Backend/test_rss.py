import time
import httpx
import asyncio

async def test_rss():
    url = "https://news.google.com/rss/search?q=latest+news&hl=en-US&gl=US&ceid=US:en"
    start = time.time()
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            print(f"Status: {resp.status_code}")
            print(f"Time taken: {time.time() - start:.2f} seconds")
        except Exception as e:
            print(f"Error: {e}")
            print(f"Time taken before error: {time.time() - start:.2f} seconds")

if __name__ == "__main__":
    asyncio.run(test_rss())
