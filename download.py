import abc
import asyncio
import base64
import hashlib
import os
import random
import time
import urllib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, Sequence
from urllib.parse import urlparse

import httpx
from platformdirs import PlatformDirs

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
PROXY_BASE = base64.b64decode("aHR0cHM6Ly9nb3ByZWZsaWdodC5jby5uei9kYXRhL2NoYXJ0Lw==").decode("utf-8")

DOWNLOAD_CACHE_DIR = PlatformDirs("kiwiAIRAC", False).user_cache_path
CACHE_EXPIRY_DAYS = 7

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
		return url.startswith("https://www.aip.net.nz/")

	def get_proxy_url(self, url: str) -> str:
		encoded_url = urllib.parse.quote_plus(url)
		return f"{self.base_url}{encoded_url}"

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
	content_types: Optional[Sequence[str]] = None

	@property
	def filename(self) -> str:
		parsed = urlparse(self.url)
		ext = Path(parsed.path).suffix  # includes leading "."
		digest = hashlib.sha256(self.url.encode("utf-8")).hexdigest()[:24]
		return f"{digest}{ext or ''}"

class _DownloadManager:
	def __init__(
		self,
		download_dir: Path,
		user_agent: str,
		proxy: Proxy | None = None,
		cache_expiry_days: int = CACHE_EXPIRY_DAYS,
		concurrency: int = 8,
		rps: float = 4.0,
		timeout: float = 30.0,
		max_retries: int = 3,
	):
		self._download_dir = download_dir
		if not self._download_dir.exists():
			self._download_dir.mkdir(parents=False)

		self._rate_limiter = _RateLimiter(rps=rps)
		self._max_retries = max_retries
		self._proxy = proxy
		self._cache_expiry_seconds = cache_expiry_days * 24 * 3600

		limits = httpx.Limits(
			max_connections=concurrency * 2,
			max_keepalive_connections=concurrency,
			keepalive_expiry=30,
		)

		self._client = httpx.AsyncClient(
			timeout=httpx.Timeout(timeout),
			follow_redirects=True,
			headers={"User-Agent": user_agent},
			limits=limits,
		)

		# Semaphore to limit concurrent downloads
		self._semaphore = asyncio.Semaphore(concurrency)

		# Prevent duplicate concurrent downloads of the *same* cache path
		self._inflight_lock = asyncio.Lock()
		self._inflight: dict[Path, asyncio.Task[Path]] = {}

	async def download(self, job: DownloadJob) -> Path:
		"""
		Returns a local cached file path. If cached copy is fresh, returns immediately.
		Otherwise, downloads (with retries) into the cache dir and returns the path.
		"""
		cache_path = self._download_dir / job.filename
		if self._is_fresh(cache_path):
			return cache_path

		# De-dupe concurrent downloads to the same file
		async with self._inflight_lock:
			existing = self._inflight.get(cache_path)
			if existing is None:
				task = asyncio.create_task(self._download_to_cache(job, cache_path))
				self._inflight[cache_path] = task
				existing = task

		try:
			return await existing
		finally:
			# Clean up inflight map when done (only by the last waiter)
			if existing.done():
				async with self._inflight_lock:
					await self._inflight.pop(cache_path, None)

	async def download_many(self, jobs: Iterable[DownloadJob]) -> tuple[Path]:
		tasks = [asyncio.create_task(self.download(job)) for job in jobs]
		return await asyncio.gather(*tasks)

	def _is_fresh(self, path: Path) -> bool:
		if not path.exists():
			return False
		age = time.time() - path.stat().st_mtime
		return age < self._cache_expiry_seconds

	def _rewrite_url_if_needed(self, url: str) -> str:
		if self._proxy and self._proxy.should_proxy(url):
			return self._proxy.get_proxy_url(url)
		return url

	async def _download_to_cache(self, job: DownloadJob, cache_path: Path) -> Path:
		# Another check in case someone else refreshed it while we waited for inflight lock
		if self._is_fresh(cache_path):
			return cache_path

		url = self._rewrite_url_if_needed(job.url)

		async with self._semaphore:
			await self._rate_limiter.acquire()
			await self._download_with_retries(job, url, cache_path)

		return cache_path

	async def _download_with_retries(self, job: DownloadJob, url: str, dest: Path) -> None:
		last_exc: Optional[Exception] = None

		for attempt in range(self._max_retries + 1):
			try:
				tmp = dest.with_suffix(dest.suffix + ".part")
				try:
					tmp.unlink()
				except FileNotFoundError:
					pass

				async with self._client.stream("GET", url) as resp:
					resp.raise_for_status()

					if job.content_types:
						ct = resp.headers.get("Content-Type", "")
						if not ct or not _content_type_matches(ct, job.content_types):
							raise ValueError(
								f"Unexpected Content-Type {ct!r} for {url}; expected one of {list(job.content_types)}"
							)

					with open(tmp, "wb") as f:
						async for chunk in resp.aiter_bytes(chunk_size=64 * 1024):
							if not chunk:
								continue
							f.write(chunk)

				os.replace(tmp, dest)
				return

			except (httpx.TimeoutException, httpx.TransportError, httpx.HTTPStatusError) as e:
				last_exc = e
				if attempt >= self._max_retries:
					break
				backoff = (2 ** attempt) * 0.5 + random.random() * 0.25
				await asyncio.sleep(backoff)

		assert last_exc is not None
		raise last_exc

def _content_type_matches(actual: str, expected: Iterable[str]) -> bool:
	actual_main = actual.split(";", 1)[0].strip().lower()
	for exp in expected:
		if actual_main == exp.lower():
			return True
	return False

downloader = _DownloadManager(
	download_dir=Path(DOWNLOAD_CACHE_DIR),
	user_agent=USER_AGENT,
	proxy=_AIPProxy(PROXY_BASE),
)
