from playwright.sync_api import sync_playwright
import os
import time

PROFILE_DIR = os.path.join("./data/merx", "merx_profile")
AUTH_STATE = "./merx_auth.json"
MERX_AUTH_URL = "https://www.merx.com/public/authentication"
IDP_HOST = "idp.merx.com"

os.makedirs(PROFILE_DIR, exist_ok=True)


def try_autofill_and_submit(page, username, password):
    try:
        # Try common selectors for username/email and password
        user_input = page.query_selector("input[type=\"email\"]") or page.query_selector("input[name='username']") or page.query_selector("input[name='email']") or page.query_selector("input[id*='user']")
        pass_input = page.query_selector("input[type=\"password\"]") or page.query_selector("input[name='password']") or page.query_selector("input[id*='pass']")
        if user_input and pass_input:
            user_input.fill(username)
            pass_input.fill(password)
            # try to click submit
            submit = page.query_selector("button[type='submit']") or page.query_selector("input[type='submit']") or (page.locator("text=Sign in").first if page.locator("text=Sign in").count() > 0 else None)
            if submit:
                try:
                    submit.click()
                except Exception:
                    # fallback: press Enter in password field
                    pass_input.press('Enter')
                return True
    except Exception:
        pass
    return False


if __name__ == '__main__':
    with sync_playwright() as p:
        print("Launching persistent browser profile for manual login...")
        context = p.chromium.launch_persistent_context(user_data_dir=PROFILE_DIR, headless=False, slow_mo=80)
        page = context.new_page()

        # Start SSO from the MERX authentication entry so the SP issues a fresh SAML request
        print(f"Navigating to MERX auth entry: {MERX_AUTH_URL}")
        page.goto(MERX_AUTH_URL)
        page.wait_for_load_state('networkidle')

        # Try to find and click a login/link that triggers SSO to the IdP
        clicked = False
        try:
            # common link/button patterns that lead to SSO
            link = page.query_selector("a[href*='idp.merx.com']") or page.query_selector("button:has-text('Sign in')") or page.query_selector("a:has-text('Sign in')") or page.locator("text=Sign in").first
            if link:
                try:
                    link.click()
                    clicked = True
                except Exception:
                    pass
        except Exception:
            pass

        if not clicked:
            # try alternative navigation: click any login button or wait for automatic redirect
            try:
                alt = page.locator("text=Sign in").first
                if alt.count() > 0:
                    alt.click()
                    clicked = True
            except Exception:
                clicked = False

        # Wait for redirect to IdP host (fresh SAML request). If not redirected, navigate to MERX auth URL again.
        try:
            page.wait_for_url(f"**{IDP_HOST}**", timeout=20000)
            print("Redirected to IdP host.")
        except Exception:
            print("Did not redirect to IdP automatically; attempting to navigate to MERX auth again.")
            page.goto(MERX_AUTH_URL)
            page.wait_for_load_state('networkidle')

        # If we are on the IdP host, attempt autofill or pause for manual login
        user = os.getenv('MERX_USER')
        pwd = os.getenv('MERX_PASS')
        autofilled = False
        if IDP_HOST in page.url and user and pwd:
            print("On IdP page and credentials available; attempting autofill...")
            autofilled = try_autofill_and_submit(page, user, pwd)
            if autofilled:
                print("Credentials submitted, waiting for redirect...")
                try:
                    page.wait_for_load_state('networkidle', timeout=60000)
                except Exception:
                    pass

        if not autofilled:
            # If not on IdP yet, wait for user to be redirected and then allow manual login
            if IDP_HOST not in page.url:
                print("Waiting for redirect to IdP for manual login. If nothing happens, click the login link in the opened browser.")
                try:
                    page.wait_for_url(f"**{IDP_HOST}**", timeout=120000)
                except Exception:
                    print("Timed out waiting for IdP redirect.")

            print("Please complete the login manually in the opened browser window(s).")
            try:
                page.pause()
            except Exception:
                pass
            while True:
                resp = input("Type 'done' and press Enter when you have completed login: ").strip().lower()
                if resp == 'done':
                    break
                print("Waiting for you to finish login... type 'done' when finished.")

        # Save authenticated state
        try:
            context.storage_state(path=AUTH_STATE)
            print(f"Saved auth state to {AUTH_STATE}")
        except Exception as e:
            print(f"Warning: failed to save storage state: {e}")

        # keep browser open briefly so user can inspect
        time.sleep(1)
        context.close()
        print("Login helper finished.")
