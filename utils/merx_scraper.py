from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json
import os
import time
import random
from urllib.parse import urljoin
import re

DATA_DIR = "./data/merx"
AUTH_STATE = "./merx_auth.json"
BASE_URL = "https://www.merx.com"
SEARCH_URL = "https://www.merx.com/private/supplier/solicitations/search"

os.makedirs(DATA_DIR, exist_ok=True)


def parse_list_page(html):
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", id="solicitationsTable")
    results = []
    if not table:
        return results
    for tr in table.select("tbody > tr"):
        # Skip empty-note row
        if "mets-table-row-empty" in (" ".join(tr.get("class", []))):
            continue
        try:
            title_a = tr.select_one("span.solicitationTitle a")
            title = title_a.get_text(strip=True) if title_a else None
            href = title_a.get("href") if title_a else None
            page_url = urljoin(BASE_URL, href) if href else None

            # Try to extract solicitation id from inline script JSON (awsMetricsAdditionalData) or from href
            sol_id = None
            # look for nearby script tag containing awsMetricsAdditionalData
            script = None
            for s in tr.find_all("script"):
                txt = s.string or ""
                if "awsMetricsAdditionalData" in txt:
                    script = txt
                    break
            if script:
                m = re.search(r'awsMetricsAdditionalData\s*=\s*"(\{.*?\})"', script)
                if m:
                    # the JSON is HTML-escaped inside a string; unescape quotes and parse
                    jtext = m.group(1).encode("utf-8" ).decode("unicode_escape")
                    try:
                        data = json.loads(jtext.replace("\'", "\"") )
                        sol_id = data.get("solicitationId")
                    except Exception:
                        sol_id = None
                else:
                    # fallback: try to extract JSON-like object in the script
                    m2 = re.search(r'awsMetricsAdditionalData\s*=\s*(\{.*?\})', script)
                    if m2:
                        try:
                            data = json.loads(m2.group(1))
                            sol_id = data.get("solicitationId")
                        except Exception:
                            sol_id = None

            if not sol_id and href:
                m = re.search(r'/open-solicitation/(\d+)', href)
                if m:
                    sol_id = m.group(1)
                else:
                    # some links use interception/view-notice/<id>
                    m2 = re.search(r'/(?:view-notice|open-solicitation)/(\d+)', href)
                    if m2:
                        sol_id = m2.group(1)

            buyer = (tr.select_one("span.buyerIdentification").get_text(strip=True) if tr.select_one("span.buyerIdentification") else None)
            closing = (tr.select_one("span.dateValue").get_text(strip=True) if tr.select_one("span.dateValue") else None)
            region = (tr.select_one("span.regionValue").get_text(strip=True) if tr.select_one("span.regionValue") else None)
            pub = None
            pub_el = tr.select_one("span.publicationDate")
            if pub_el:
                pub = pub_el.get_text(strip=True).replace("Published Date", "").strip()

            short_desc = tr.select_one("span.solicitationDescription")
            short_desc = short_desc.get_text(strip=True) if short_desc else None
            mandatory = bool(tr.select_one("span.mandatory"))

            results.append({
                "solicitation_id": sol_id,
                "title": title,
                "page_url": page_url,
                "buyer": buyer,
                "closing_date": closing,
                "region": region,
                "published_date": pub,
                "short_description": short_desc,
                "mandatory_pre_bid": mandatory,
            })
        except Exception:
            continue
    return results


def run(max_pages=None, headless=False):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)

        # Use persistent profile or existing storage state. Open a visible browser so you can log in manually.
        profile_dir = os.path.join(DATA_DIR, "merx_profile")
        os.makedirs(profile_dir, exist_ok=True)

        if os.path.exists(AUTH_STATE):
            # Reuse saved auth state if available
            context = browser.new_context(storage_state=AUTH_STATE)
        else:
            print("No saved auth state found. A browser window will open for manual MERX login.")
            # Launch persistent context so your manual login persists in profile_dir
            # Use slow_mo when headless to make interaction easier
            slow = 0 if headless else 50
            context = p.chromium.launch_persistent_context(user_data_dir=profile_dir, headless=headless, slow_mo=slow)

            # Log page open/close events and pause new pages so SSO popups don't disappear
            def _on_new_page(paged):
                try:
                    print(f"[debug] New page opened: {paged.url}")
                except Exception:
                    print("[debug] New page opened (url not available yet)")
                try:
                    paged.bring_to_front()
                    paged.pause()
                except Exception as e:
                    print(f"[debug] failed to pause new page: {e}")

            def _on_close_page(paged):
                try:
                    print(f"[debug] Page closed: {paged.url}")
                except Exception:
                    print("[debug] Page closed")

            try:
                context.on("page", _on_new_page)
            except Exception:
                pass
            try:
                context.on("close", _on_close_page)
            except Exception:
                pass

            # Open a page for you to interactively log in
            page = context.new_page()
            page.goto("https://www.merx.com/public/authentication")
            print("Browser opened for manual login. Complete the login and any SSO popups/tabs.")
            # Wait until user confirms completion
            while True:
                resp = input("Type 'done' and press Enter when you have completed login: ").strip().lower()
                if resp == 'done':
                    break
                print("Waiting for you to finish login... type 'done' when finished.")

            # Save storage state after manual login for future runs
            try:
                context.storage_state(path=AUTH_STATE)
                print(f"Saved auth state to {AUTH_STATE}")
            except Exception as e:
                print(f"Warning: failed to save storage state: {e}")

        page = context.new_page()

        
        # Navigate from the authenticated homepage and click the solicitations link to reproduce normal client flow
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        time.sleep(1)

        # Try to accept cookie banner if present (common labels)
        try:
            cookie_btn = page.query_selector("button:has-text('Accept')") or page.query_selector("button:has-text('I agree')") or page.query_selector("button:has-text('Accept all')")
            if cookie_btn:
                cookie_btn.click()
                time.sleep(0.5)
        except Exception:
            pass

        # Try to find and click a link that leads to the private solicitations/search area
        clicked = False
        try:
            # common href patterns
            link = page.query_selector("a[href*='/private/supplier/solicitations']") or page.query_selector("a[href*='/solicitations']")
            if link:
                link.click()
                page.wait_for_load_state("networkidle")
                clicked = True
        except Exception:
            clicked = False

        # Fallback: try clicking by visible text
        if not clicked:
            try:
                txt_link = page.locator("text=Solicitations").first
                if txt_link.count() > 0:
                    txt_link.click()
                    page.wait_for_load_state("networkidle")
                    clicked = True
            except Exception:
                clicked = False

        # If navigation didn't work, fall back to direct SEARCH_URL (with debug)
        if not clicked:
            resp = page.goto(SEARCH_URL)
            print(f"DEBUG: fallback goto status={resp.status if resp else None}, url={page.url}")
        else:
            # Wait for the solicitations table to appear (may be loaded via AJAX)
            try:
                page.wait_for_selector("table#solicitationsTable", timeout=10000)
            except Exception:
                # Save a screenshot for diagnostics
                try:
                    screenshot_path = os.path.join(DATA_DIR, "debug_after_nav.png")
                    page.screenshot(path=screenshot_path)
                    print(f"Saved debug screenshot to {screenshot_path}")
                except Exception:
                    pass
                # last resort: try direct goto
                resp = page.goto(SEARCH_URL)
                print(f"DEBUG: after click fallback goto status={resp.status if resp else None}, url={page.url}")

        # Short wait to ensure JS-rendered content is ready
        time.sleep(1)

        # Diagnostic dump: save response status, final URL, snippet and full HTML and a screenshot
        try:
            status = None
            if 'resp' in locals() and resp:
                try:
                    status = resp.status
                except Exception:
                    status = None
            url = page.url if page else ''
            snippet = (page.content() or '')[:2000]
            with open(os.path.join(DATA_DIR, 'debug_status.txt'), 'w', encoding='utf-8') as _f:
                _f.write(f"status: {status}\nurl: {url}\n")
            with open(os.path.join(DATA_DIR, 'debug_snippet.txt'), 'w', encoding='utf-8') as _f:
                _f.write(snippet)
            with open(os.path.join(DATA_DIR, 'debug_full.html'), 'w', encoding='utf-8') as _f:
                _f.write(page.content() or '')
            try:
                screenshot_path = os.path.join(DATA_DIR, 'debug.png')
                page.screenshot(path=screenshot_path)
                print(f"Saved debug screenshot to {screenshot_path}")
            except Exception as e:
                print(f"Failed to save screenshot: {e}")
        except Exception as de:
            print(f"Diagnostics dump failed: {de}")

        # Interactive mode: allow manual actions (e.g., clicking Search) when PWDEBUG set or INTERACTIVE=1
        try:
            interactive = os.getenv('INTERACTIVE', '0') == '1' or os.getenv('PWDEBUG') is not None
        except Exception:
            interactive = False

        if not headless and interactive:
            print("Interactive mode enabled. Please ensure the solicitations list is visible in the opened browser.")
            try:
                page.pause()
            except Exception:
                pass
            while True:
                resp = input("Type 'done' and press Enter when the solicitations list is visible: ").strip().lower()
                if resp == 'done':
                    break
                print("Waiting... type 'done' when ready.")

        # Wait for table rows to be present (allow JS/XHR to populate the table)
        try:
            page.wait_for_selector("table#solicitationsTable tbody > tr", timeout=30000)
        except Exception:
            print("Warning: table rows did not appear within 30s; proceeding to parse whatever is present.")

        
        all_records = []
        page_idx = 1
        while True:
            print(f"Scraping page {page_idx}...")
            html = page.content()

            # Save raw HTML
            page_file = os.path.join(DATA_DIR, f"page_{page_idx}.html")
            with open(page_file, "w", encoding="utf-8") as f:
                f.write(html)

            records = parse_list_page(html)
            all_records.extend(records)

            # Save parsed JSON for this page
            json_file = os.path.join(DATA_DIR, f"page_{page_idx}.json")
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(records, f, ensure_ascii=False, indent=2)

            # Check max_pages limit
            if max_pages and page_idx >= max_pages:
                print(f"Reached max_pages limit: {max_pages}. Stopping.")
                break

            # Try to navigate to next page; attempt common selectors for a "Next" control
            next_clicked = False
            try:
                next_locator = page.locator("text=Next").first
                if next_locator.count() > 0:
                    next_locator.click()
                    next_clicked = True
            except Exception:
                pass

            if not next_clicked:
                try:
                    el = page.query_selector('a[rel="next"]') or page.query_selector('a.next') or page.query_selector('.pagination .next')
                    if el:
                        el.click()
                        next_clicked = True
                except Exception:
                    next_clicked = False

            if not next_clicked:
                print("No next page control found or reached last page. Stopping pagination.")
                break

            # polite delay
            page_idx += 1
            time.sleep(1 + random.random() * 2)
            page.wait_for_load_state("networkidle")

        # Save aggregate results
        out_file = os.path.join(DATA_DIR, "all_results.json")
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(all_records, f, ensure_ascii=False, indent=2)

        print(f"Scraped {len(all_records)} records. Saved to {out_file}")
        context.close()
        browser.close()


if __name__ == "__main__":
    # Example: run headful so you can login if needed and paginate until exhausted
    run(max_pages=None, headless=False)
