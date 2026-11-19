"""Exercise the solar ledger at a project subpath in Chromium."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import os
import shutil
import tempfile
import threading
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def main():
    screenshots = ROOT / "browser-checks"
    screenshots.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as temporary:
        shutil.copytree(ROOT / "dist", Path(temporary) / "example-tool")
        server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=temporary))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(executable_path=os.environ.get("CHROMIUM_BIN"))
                page = browser.new_page(viewport={"width": 1280, "height": 1000})
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.goto(f"http://127.0.0.1:{server.server_port}/example-tool/")
                page.locator('#work').wait_for(state='visible')
                assert page.locator('#chosen').inner_text() == 'December'
                assert page.locator('#langley').inner_text() == '0.68'
                assert page.locator('#halifax').inner_text() == '1.14'
                page.locator('#month').select_option('6')
                assert page.locator('#langley').inner_text() == '5.52'
                assert page.locator('#halifax').inner_text() == '5.53'
                page.locator('#period').select_option('2024')
                assert page.locator('#langley').inner_text() != '5.52'
                page.locator('#benchmark').uncheck()
                assert not page.locator('#langley-ref').is_visible()
                page.locator('#month-summary').click()
                assert page.locator('#history tr.current th').inner_text() == '2024'
                assert page.locator('#history tr.current td').first.inner_text() == page.locator('#langley').inner_text()
                page.locator('#month-summary').click()
                page.get_by_text('Annual means by year', exact=True).click()
                assert page.locator('#annual tr.current td').first.inner_text() != '—'
                page.get_by_text('Annual means by year', exact=True).click()
                page.locator('#benchmark').check()
                page.locator('#period').select_option('2001–2020')
                page.locator('#month').select_option('12')
                page.screenshot(path=str(screenshots / 'desktop.png'), full_page=True)
                page.set_viewport_size({'width': 375, 'height': 812})
                assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
                page.locator('#chart rect[cursor]').nth(5).click()
                assert page.locator('#chosen').inner_text() == 'June'
                page.screenshot(path=str(screenshots / 'mobile.png'), full_page=True)
                assert not errors, errors
                browser.close()
            print("Browser checks passed: month, year, benchmark, source rows and mobile chart")
        finally:
            server.shutdown()


if __name__ == "__main__":
    main()
