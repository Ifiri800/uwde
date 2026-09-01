from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright


@dataclass
class BrowserPage:
    url: str
    title: str
    html: str
    text: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "title": self.title,
            "html": self.html,
            "text": self.text,
        }


class BrowserAutomation:
    """
    Controlled browser automation service for JavaScript-rendered pages.

    The service owns the Playwright lifecycle and provides a small,
    testable abstraction to the rest of UWDE.
    """

    def __init__(
        self,
        *,
        headless: bool = True,
        timeout_ms: int = 30_000,
    ) -> None:
        if timeout_ms <= 0:
            raise ValueError("timeout_ms must be greater than zero.")

        self.headless = headless
        self.timeout_ms = timeout_ms

        self._playwright = None
        self._browser: Browser | None = None

    def start(self) -> None:
        if self._browser is not None:
            return

        self._playwright = sync_playwright().start()

        self._browser = self._playwright.chromium.launch(
            headless=self.headless,
        )

    def close(self) -> None:
        if self._browser is not None:
            self._browser.close()
            self._browser = None

        if self._playwright is not None:
            self._playwright.stop()
            self._playwright = None

    def __enter__(self) -> "BrowserAutomation":
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    def _require_browser(self) -> Browser:
        if self._browser is None:
            raise RuntimeError(
                "BrowserAutomation is not started."
            )

        return self._browser

    def create_context(self) -> BrowserContext:
        browser = self._require_browser()

        context = browser.new_context()

        context.set_default_timeout(self.timeout_ms)

        return context

    def open_page(self, url: str) -> BrowserPage:
        if not url or not url.strip():
            raise ValueError("URL cannot be empty.")

        context = self.create_context()

        try:
            page = context.new_page()

            page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=self.timeout_ms,
            )

            title = page.title()
            html = page.content()
            text = page.locator("body").inner_text()

            return BrowserPage(
                url=page.url,
                title=title,
                html=html,
                text=text,
            )

        finally:
            context.close()

    def open_interactive_page(self, url: str) -> Page:
        """
        Open a page and return the Playwright Page object.

        The caller owns the returned context/page and must close the
        context when finished.
        """

        if not url or not url.strip():
            raise ValueError("URL cannot be empty.")

        context = self.create_context()
        page = context.new_page()

        page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=self.timeout_ms,
        )

        return page

    def load_more(
        self,
        url: str,
        selector: str = "button#load-more, a#load-more, .load-more, [data-load-more]",
    ) -> BrowserPage:
        """
        Open a page, click a Load More control, and return the
        resulting rendered page.
        """

        if not url or not url.strip():
            raise ValueError("URL cannot be empty.")

        context = self.create_context()

        try:
            page = context.new_page()

            page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=self.timeout_ms,
            )

            control = page.locator(selector).first

            if control.count() == 0:
                raise RuntimeError(
                    "Load More control was not found."
                )

            before_html = page.content()

            control.click(
                timeout=self.timeout_ms,
            )

            page.wait_for_function(
                """
                (previousHtml) => document.documentElement.outerHTML !== previousHtml
                """,
                before_html,
                timeout=self.timeout_ms,
            )

            return BrowserPage(
                url=page.url,
                title=page.title(),
                html=page.content(),
                text=page.locator("body").inner_text(),
            )

        finally:
            context.close()

    def infinite_scroll(
        self,
        url: str,
        scroll_count: int = 1,
        scroll_distance: int = 1200,
    ) -> BrowserPage:
        """
        Open a page, perform bounded scrolling, and return the
        resulting rendered page.
        """

        if not url or not url.strip():
            raise ValueError("URL cannot be empty.")

        if scroll_count <= 0:
            raise ValueError(
                "scroll_count must be greater than zero."
            )

        if scroll_distance <= 0:
            raise ValueError(
                "scroll_distance must be greater than zero."
            )

        context = self.create_context()

        try:
            page = context.new_page()

            page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=self.timeout_ms,
            )

            for _ in range(scroll_count):
                before_height = page.evaluate(
                    "document.body.scrollHeight"
                )

                page.evaluate(
                    "(distance) => window.scrollBy(0, distance)",
                    scroll_distance,
                )

                try:
                    page.wait_for_function(
                        """
                        (previousHeight) =>
                            document.body.scrollHeight > previousHeight
                        """,
                        before_height,
                        timeout=min(
                            self.timeout_ms,
                            5_000,
                        ),
                    )
                except Exception:
                    pass

            return BrowserPage(
                url=page.url,
                title=page.title(),
                html=page.content(),
                text=page.locator("body").inner_text(),
            )

        finally:
            context.close()
