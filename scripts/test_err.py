import asyncio
import httpx
import re

async def fetch_exact_error(url: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # We use localhost here for testing outside container, backend will use monitoring-blackbox
            resp = await client.get(f"http://localhost:9115/probe", params={"target": url, "debug": "true", "module": "http_2xx"})
            text = resp.text
            errors = []
            for line in text.split('\n'):
                if 'level=error' in line and 'err=' in line:
                    match = re.search(r'err="([^"]+)"', line)
                    if match:
                        err_str = match.group(1).replace('\\"', '"')
                        if err_str not in errors:
                            errors.append(err_str)
            if errors:
                return " | ".join(errors)
            return "Unknown error from probe logs"
    except Exception as e:
        return f"Fetch log error: {str(e)}"

async def main():
    urls = [
        "https://admin.corona.jatengprov.go.id/",
        "https://akd.bpsdmd.jatengprov.go.id/"
    ]
    tasks = [fetch_exact_error(u) for u in urls]
    results = await asyncio.gather(*tasks)
    for u, r in zip(urls, results):
        print(f"{u} -> {r}")

if __name__ == "__main__":
    asyncio.run(main())
