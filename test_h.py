import asyncio
import httpx
async def test():
    async with httpx.AsyncClient(follow_redirects=True) as client:
        r = await client.get('https://docs.google.com/spreadsheets/d/1hbvUroW0SxAbTbsn0nn-9wJyYKz-zLDJQ_PS7b83SzA/export?format=csv&gid=1833845756', headers={'User-Agent': 'Mozilla/5.0'})
        print(r.status_code)
        print(len(r.text))
        print(r.text[:100])
asyncio.run(test())
