import abc
import asyncio
import base64
import os
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

import httpx

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
PROXY_BASE = base64.b64decode("aHR0cHM6Ly9nb3ByZWZsaWdodC5jby5uei9kYXRhL2NoYXJ0Lw").decode("utf-8")

class Proxy(abc.ABC):
	@abc.abstractmethod
	def should_proxy(self, url: str) -> bool:
		"""Returns True if the given URL should be proxied, False otherwise."""
		pass

	@abc.abstractmethod
	def get_proxy_url(self, url: str) -> str:
		"""Returns the URL to proxy the given URL through."""
		pass

class _AIPProxy(Proxy):
	"""
	A simple proxy client that forwards requests to the AIP server.
	This is necessary to avoid CORS issues when making requests from the browser.
	"""
	def __init__(self, base_url: str):
		self.base_url = base_url

	def should_proxy(self, url: str) -> bool:
		# Only proxy requests to the AIP server
		return url.startswith("https://www.aip.net.nz/")

	def get_proxy_url(self, url: str) -> str:
		# Encode the original URL as a query parameter
		return f"{self.base_url}{url}"

class _RateLimiter:
	"""
	Global requests-per-second limiter.
	"""
	def __init__(self, rps: float):
		self.rps = float(rps)
		self._lock = asyncio.Lock()
		self._next_allowed = 0.0  # monotonic time

	async def acquire(self) -> None:
		if self.rps <= 0:
			return
		interval = 1.0 / self.rps
		async with self._lock:
			now = time.monotonic()
			if now < self._next_allowed:
				await asyncio.sleep(self._next_allowed - now)
				now = time.monotonic()
			self._next_allowed = max(self._next_allowed, now) + interval

@dataclass(frozen=True)
class DownloadJob:
	url: str
	dest: Path
	content_types: Optional[Iterable[str]] = None

class _DownloadManager:
	def __init__(
		self,
		user_agent: str,
		proxy: Proxy | None = None,
		concurrency: int = 8,
		rps: float = 4.0,
		timeout: float = 30.0,
		max_retries: int = 3,
	):
		self._rate_limiter = _RateLimiter(rps=rps)
		self._max_retries = max_retries
		self._proxy = proxy

		limits = httpx.Limits(
			max_connections=concurrency * 2,
			max_keepalive_connections=concurrency,
			keepalive_expiry=30,
		)

		self.client = httpx.AsyncClient(
			timeout=httpx.Timeout(timeout),
			follow_redirects=True,
			headers={"User-Agent": user_agent},
			limits=limits,
		)

		self._semaphore = asyncio.Semaphore(concurrency)

	async def download(self, job: DownloadJob) -> Path:
		job.dest.parent.mkdir(parents=True, exist_ok=True)

		url = self._rewrite_url_if_needed(job.url)

		async with self._semaphore:
			await self._rate_limiter.acquire()
			return await self._download_with_retries(url, job.dest)

	async def download_many(self, jobs: Iterable[DownloadJob]) -> tuple[Path]:
		tasks = [asyncio.create_task(self.download(job)) for job in jobs]
		return await asyncio.gather(*tasks)

	def _rewrite_url_if_needed(self, url: str) -> str:
		if self._proxy and self._proxy.should_proxy(url):
			return self._proxy.get_proxy_url(url)
		return url

	async def _download_with_retries(self, url: str, dest: Path) -> Path:
		last_exc: Optional[Exception] = None

		for attempt in range(self._max_retries + 1):
			try:
				tmp = dest.with_suffix(dest.suffix + ".part")
				if tmp.exists():
					tmp.unlink(missing_ok=True)

				async with self.client.stream("GET", url) as resp:
					resp.raise_for_status()

					with open(tmp, "wb") as f:
						async for chunk in resp.aiter_bytes(chunk_size=64 * 1024):
							if not chunk:
								continue
							f.write(chunk)

				os.replace(tmp, dest)
				return dest

			except (httpx.TimeoutException, httpx.TransportError, httpx.HTTPStatusError) as e:
				last_exc = e
				if attempt >= self._max_retries:
					break
				# Exponential backoff + jitter
				backoff = (2 ** attempt) * 0.5 + random.random() * 0.25
				await asyncio.sleep(backoff)

		assert last_exc is not None
		raise last_exc

download_manager = _DownloadManager(USER_AGENT, proxy=_AIPProxy(PROXY_BASE))
