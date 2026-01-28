'''from playwright.sync_api import sync_playwright
import time
import os
import json
import re
from datetime import datetime

class EnterpriseScraper:
    def __init__(self):
        self.base_dir = os.getcwd()
        self.evidence_dir = os.path.join(self.base_dir, "evidence")
        if not os.path.exists(self.evidence_dir):
            os.makedirs(self.evidence_dir)

    def load_cookies(self, context):
        cookie_file = "cookies.json"
        if os.path.exists(cookie_file):
            try:
                with open(cookie_file, 'r') as f:
                    cookies = json.load(f)
                    for c in cookies:
                        if 'sameSite' in c and c['sameSite'] not in ["Strict", "Lax", "None"]:
                            c['sameSite'] = "None"
                    context.add_cookies(cookies)
                print("🍪 Session Cookies Injected.")
                return True
            except: return False
        return False

    def clean_text(self, text):
        lines = text.split('\n')
        valid_lines = []
        garbage = ["Reply", "See translation", "View all", "Log in", "Sign up", "Liked by", "View more", "Hide"]
        for line in lines:
            l = line.strip()
            if re.match(r'^\d+[hmwd]$', l): continue
            if "likes" in l and len(l) < 15: continue
            if len(l) < 2: continue
            if any(g in l for g in garbage): continue
            valid_lines.append(l)
        if not valid_lines: return None
        return max(valid_lines, key=len)

    def perform_page_end_scroll(self, page):
        """Clicks safe area and hits End to scroll main feed"""
        try:
            page.mouse.click(10, 10) 
            page.keyboard.press("End")
            time.sleep(1.5) 
            return True
        except Exception as e:
            print(f"⚠️ Scroll error: {e}")
            return False

    # ---------------------------------------------------------
    # NEW: Active Expansion Logic
    # ---------------------------------------------------------
    def expand_threads(self, page):
        """
        Locates 'View replies', 'View more', or 'Hidden comments' buttons
        and clicks them to load the actual text into the DOM.
        """
        try:
            # 1. Handle "View hidden comments" (The specific offensive/spam bucket)
            # This is critical for your use case as toxic comments often land here
            hidden_btns = page.locator("text='View hidden comments'").all()
            for btn in hidden_btns:
                if btn.is_visible():
                    print("  Found hidden comments section... expanding.")
                    btn.click()
                    time.sleep(1.5) # Wait for fetch

            # 2. Handle "View replies" (Nested threads)
            # We look for buttons that look like "View replies (3)"
            # Note: We limit this to 3 clicks per scroll to prevent the script from getting stuck forever on one post
            reply_btns = page.locator("div[role='button']:has-text('View replies')").all()
            
            for i, btn in enumerate(reply_btns):
                if i > 3: break # Performance Governor: Only open top 3 threads per scroll batch
                if btn.is_visible():
                    try:
                        btn.scroll_into_view_if_needed()
                        btn.click()
                        time.sleep(0.5) # Short wait for DOM update
                    except: pass
            
            # 3. Handle "more" (Truncated long text)
            more_btns = page.locator("text='more'").all()
            for btn in more_btns:
                if btn.is_visible():
                    try:
                        btn.click()
                    except: pass
                    
        except Exception as e:
            # We silently ignore expansion errors to keep the main scraper running
            pass

    def run(self, url, max_limit, analyzer):
        findings = []
        count = 0
        seen_comments = set()
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        with sync_playwright() as p:
            print("🚀 Launching Scraper...")
            
            iphone = p.devices['iPhone 13 Pro'].copy()
            iphone['viewport'] = {'width': 390, 'height': 844}
            
            browser = p.chromium.launch(headless=False, channel="msedge", args=["--disable-blink-features=AutomationControlled"])
            context = browser.new_context(**iphone)
            self.load_cookies(context)
            page = context.new_page()
            
            try:
                print(f"🌍 Opening: {url}")
                page.goto(url, timeout=60000)
                time.sleep(6) 

                stuck_counter = 0
                last_count = 0

                while count < max_limit:
                    if page.is_closed(): break

                    # --- STEP 1: MAIN SCROLL ---
                    self.perform_page_end_scroll(page)

                    # --- STEP 2: EXPAND HIDDEN CONTENT (NEW) ---
                    # We do this AFTER scrolling but BEFORE scraping
                    self.expand_threads(page)

                    try:
                        # We grab 'li' items (comments) but also 'span' texts inside them now that they are expanded
                        comment_elements = page.locator("ul > li, div[role='button']").all()
                    except: break

                    if len(comment_elements) == last_count:
                        stuck_counter += 1
                        if stuck_counter > 20: 
                            print("✅ Reached end of visible comments.")
                            break
                    else:
                        stuck_counter = 0
                    last_count = len(comment_elements)

                    # Scan the bottom batch (increased batch size slightly to catch expanded items)
                    batch = comment_elements[-30:] if len(comment_elements) > 30 else comment_elements
                    
                    for el in batch:
                        if count >= max_limit: break
                        try:
                            if page.is_closed(): break
                            
                            raw_text = el.inner_text()
                            text = self.clean_text(raw_text)
                            if not text: continue
                            
                            if text in seen_comments: continue
                            seen_comments.add(text)

                            # Pass to your Analyzer
                            res = analyzer.scan(text)
                            
                            if res['is_toxic']:
                                print(f"🚨 MATCH: {text[:30]}... [{res['reason']}]")
                                
                                el.scroll_into_view_if_needed()
                                
                                # Highlight & Capture
                                el.evaluate("node => { node.style.border = '3px solid red'; node.style.backgroundColor = 'rgba(255,0,0,0.1)'; }")
                                img_path = os.path.join(self.evidence_dir, f"evidence_{session_id}_{count}.png")
                                page.screenshot(path=img_path)
                                el.evaluate("node => { node.style.border = ''; node.style.backgroundColor = ''; }")

                                findings.append({
                                    "text": text, 
                                    "reason": res['reason'], 
                                    "link": url, 
                                    "image": img_path
                                })
                                count += 1
                        except: continue
            
            except Exception as e:
                print(f"⚠️ Error: {e}")
            
            finally:
                try: browser.close()
                except: pass
            
            return findings'''


'''from playwright.sync_api import sync_playwright
import time
import os
import json
import re
from datetime import datetime


class EnterpriseScraper:
    def __init__(self):
        self.base_dir = os.getcwd()
        self.evidence_dir = os.path.join(self.base_dir, "evidence")
        if not os.path.exists(self.evidence_dir):
            os.makedirs(self.evidence_dir)

    # ---------------------------------------------------------
    # Cookie Loader
    # ---------------------------------------------------------
    def load_cookies(self, context):
        cookie_file = "cookies.json"
        if os.path.exists(cookie_file):
            try:
                with open(cookie_file, 'r') as f:
                    cookies = json.load(f)
                    for c in cookies:
                        if 'sameSite' in c and c['sameSite'] not in ["Strict", "Lax", "None"]:
                            c['sameSite'] = "None"
                    context.add_cookies(cookies)
                print("🍪 Session Cookies Injected.")
                return True
            except Exception as e:
                print("⚠️ Cookie load failed:", e)
        return False

     # ---------------------------------------------------------
    # Text Cleaner (FIXED)
    # ---------------------------------------------------------
    def clean_text(self, text):
        lines = text.split('\n')
        valid_lines = []
        garbage = [
            "Reply", "See translation", "View all",
            "Log in", "Sign up", "Liked by",
            "View more", "Hide"
        ]

        for line in lines:
            l = line.strip()
            # Skip timestamps like 2h, 4w
            if re.match(r'^\d+[hmwd]$', l):
                continue
            # Skip "20 likes" meta data
            if "likes" in l and len(l) < 15:
                continue
            # Skip empty/tiny junk
            if len(l) < 2:
                continue
            # Skip UI buttons
            if any(g in l for g in garbage):
                continue
            
            valid_lines.append(l)

        if not valid_lines:
            return None

        # 🔴 OLD BUGGY CODE:
        # return max(valid_lines, key=len)  <-- This was discarding short curses!

        # 🟢 NEW FIXED CODE:
        # Join username + comment so we don't lose the short words.
        return " ".join(valid_lines)

    # ---------------------------------------------------------
    # 🔥 CONTINUOUS PAGE DOWN SCROLL (FIXED)
    # ---------------------------------------------------------
    def perform_continuous_scroll(self, page, presses=4):
        """
        Human-like continuous PageDown scrolling
        """
        try:
            # Ensure page focus
            page.mouse.click(200, 200)
            time.sleep(0.2)

            for _ in range(presses):
                page.keyboard.press("PageDown")
                time.sleep(0.4)  # smooth & allows lazy loading

            return True
        except Exception as e:
            print(f"⚠️ Scroll error: {e}")
            return False

    # ---------------------------------------------------------
    # Expand Threads / Hidden Content
    # ---------------------------------------------------------
    def expand_threads(self, page):
        try:
            # Hidden comments (toxic bucket)
            hidden_btns = page.locator("text='View hidden comments'").all()
            for btn in hidden_btns:
                if btn.is_visible():
                    btn.click()
                    time.sleep(1)

            # View replies
            reply_btns = page.locator(
                "div[role='button']:has-text('View replies')"
            ).all()

            for i, btn in enumerate(reply_btns):
                if i > 3:
                    break
                if btn.is_visible():
                    try:
                        btn.scroll_into_view_if_needed()
                        btn.click()
                        time.sleep(0.5)
                    except:
                        pass

            # Expand "more"
            more_btns = page.locator("text='more'").all()
            for btn in more_btns:
                if btn.is_visible():
                    try:
                        btn.click()
                    except:
                        pass

        except:
            pass

    # ---------------------------------------------------------
    # MAIN RUN
    # ---------------------------------------------------------
    def run(self, url, max_limit, analyzer):
        findings = []
        count = 0
        seen_comments = set()
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        with sync_playwright() as p:
            print("🚀 Launching Scraper...")

            iphone = p.devices['iPhone 13 Pro'].copy()
            iphone['viewport'] = {'width': 390, 'height': 844}

            browser = p.chromium.launch(
                headless=False,
                channel="msedge",
                args=["--disable-blink-features=AutomationControlled"]
            )

            context = browser.new_context(**iphone)
            self.load_cookies(context)
            page = context.new_page()

            try:
                print(f"🌍 Opening: {url}")
                page.goto(url, timeout=60000)
                time.sleep(6)

                stuck_counter = 0
                last_count = 0

                while count < max_limit:
                    if page.is_closed():
                        break

                    # 🔥 Smooth scrolling
                    self.perform_continuous_scroll(page, presses=4)

                    # Expand replies / hidden
                    self.expand_threads(page)
                    time.sleep(0.8)

                    comment_elements = page.locator(
                        "ul > li, div[role='button']"
                    ).all()

                    if len(comment_elements) == last_count:
                        stuck_counter += 1
                        if stuck_counter > 15:
                            print("✅ End of comments detected.")
                            break
                    else:
                        stuck_counter = 0

                    last_count = len(comment_elements)

                    batch = (
                        comment_elements[-30:]
                        if len(comment_elements) > 30
                        else comment_elements
                    )

                    for el in batch:
                        if count >= max_limit:
                            break
                        try:
                            raw_text = el.inner_text()
                            text = self.clean_text(raw_text)
                            if not text:
                                continue
                            if text in seen_comments:
                                continue

                            seen_comments.add(text)

                            res = analyzer.scan(text)
                            if res['is_toxic']:
                                print(f"🚨 MATCH: {text[:40]}... [{res['reason']}]")

                                el.scroll_into_view_if_needed()

                                el.evaluate("""
                                    node => {
                                        node.style.border = '3px solid red';
                                        node.style.backgroundColor = 'rgba(255,0,0,0.1)';
                                    }
                                """)

                                img_path = os.path.join(
                                    self.evidence_dir,
                                    f"evidence_{session_id}_{count}.png"
                                )

                                page.screenshot(path=img_path)

                                el.evaluate("""
                                    node => {
                                        node.style.border = '';
                                        node.style.backgroundColor = '';
                                    }
                                """)

                                findings.append({
                                    "text": text,
                                    "reason": res['reason'],
                                    "link": url,
                                    "image": img_path
                                })

                                count += 1

                        except:
                            continue

            except Exception as e:
                print(f"⚠️ Fatal error: {e}")

            finally:
                try:
                    browser.close()
                except:
                    pass

        return findings'''




from playwright.sync_api import sync_playwright
import time
import os
import json
import re
from datetime import datetime


class EnterpriseScraper:
    def __init__(self):
        self.base_dir = os.getcwd()
        self.evidence_dir = os.path.join(self.base_dir, "evidence")
        if not os.path.exists(self.evidence_dir):
            os.makedirs(self.evidence_dir)

    # ---------------------------------------------------------
    # Cookie Loader
    # ---------------------------------------------------------
    def load_cookies(self, context):
        cookie_file = "cookies.json"
        if os.path.exists(cookie_file):
            try:
                with open(cookie_file, 'r') as f:
                    cookies = json.load(f)
                    for c in cookies:
                        if 'sameSite' in c and c['sameSite'] not in ["Strict", "Lax", "None"]:
                            c['sameSite'] = "None"
                    context.add_cookies(cookies)
                print("🍪 Session Cookies Injected.")
                return True
            except Exception as e:
                print("⚠️ Cookie load failed:", e)
        return False

    # ---------------------------------------------------------
    # Text Cleaner (FIXED)
    # ---------------------------------------------------------
    def clean_text(self, text):
        lines = text.split('\n')
        valid_lines = []
        garbage = [
            "Reply", "See translation", "View all",
            "Log in", "Sign up", "Liked by",
            "View more", "Hide", "View hidden comments", # Added to ignore button text
            "View replies"
        ]

        for line in lines:
            l = line.strip()
            if re.match(r'^\d+[hmwd]$', l):
                continue
            if "likes" in l and len(l) < 15:
                continue
            if len(l) < 2:
                continue
            if any(g in l for g in garbage):
                continue
            valid_lines.append(l)

        if not valid_lines:
            return None

        return " ".join(valid_lines)
    # ---------------------------------------------------------
    # 🔥 CONTINUOUS PAGE DOWN SCROLL
    # ---------------------------------------------------------
    def perform_continuous_scroll(self, page, presses=4):
        """
        Human-like continuous PageDown scrolling
        """
        try:
            # Ensure page focus
            page.mouse.click(200, 200)
            time.sleep(0.2)

            for _ in range(presses):
                page.keyboard.press("PageDown")
                time.sleep(0.4)  # smooth & allows lazy loading

            return True
        except Exception as e:
            print(f"⚠️ Scroll error: {e}")
            return False

    # ---------------------------------------------------------
    # Expand Threads / Hidden Content
    # ---------------------------------------------------------
    def expand_threads(self, page):
        try:
            # Hidden comments (toxic bucket)
            hidden_btns = page.locator("text='View hidden comments'").all()
            for btn in hidden_btns:
                if btn.is_visible():
                    btn.click()
                    time.sleep(1)

            # View replies
            reply_btns = page.locator(
                "div[role='button']:has-text('View replies')"
            ).all()

            for i, btn in enumerate(reply_btns):
                if i > 3:
                    break
                if btn.is_visible():
                    try:
                        btn.scroll_into_view_if_needed()
                        btn.click()
                        time.sleep(0.5)
                    except:
                        pass

            # Expand "more"
            more_btns = page.locator("text='more'").all()
            for btn in more_btns:
                if btn.is_visible():
                    try:
                        btn.click()
                    except:
                        pass

        except:
            pass

    # ---------------------------------------------------------
    # MAIN RUN
    # ---------------------------------------------------------
    def run(self, url, max_limit, analyzer):
        findings = []
        count = 0
        seen_comments = set()
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        with sync_playwright() as p:
            print("🚀 Launching Scraper...")

            iphone = p.devices['iPhone 13 Pro'].copy()
            iphone['viewport'] = {'width': 390, 'height': 844}

            browser = p.chromium.launch(
                headless=False,
                channel="msedge",
                args=["--disable-blink-features=AutomationControlled"]
            )

            context = browser.new_context(**iphone)
            self.load_cookies(context)
            page = context.new_page()

            try:
                print(f"🌍 Opening: {url}")
                page.goto(url, timeout=60000)
                time.sleep(6)

                stuck_counter = 0
                last_count = 0

                while count < max_limit:
                    if page.is_closed():
                        break

                    # 🔥 Smooth scrolling
                    self.perform_continuous_scroll(page, presses=4)

                    # Expand replies / hidden
                    self.expand_threads(page)
                    time.sleep(0.8)

                    comment_elements = page.locator(
                        "ul > li, div[role='button']"
                    ).all()

                    if len(comment_elements) == last_count:
                        stuck_counter += 1
                        if stuck_counter > 15:
                            print("✅ End of comments detected.")
                            break
                    else:
                        stuck_counter = 0

                    last_count = len(comment_elements)

                    batch = (
                        comment_elements[-30:]
                        if len(comment_elements) > 30
                        else comment_elements
                    )

                    for el in batch:
                        if count >= max_limit:
                            break
                        try:
                            raw_text = el.inner_text()
                            text = self.clean_text(raw_text)
                            if not text:
                                continue
                            if text in seen_comments:
                                continue

                            seen_comments.add(text)

                            res = analyzer.scan(text)
                            if res['is_toxic']:
                                print(f"🚨 MATCH: {text[:40]}... [{res['reason']}]")

                                el.scroll_into_view_if_needed()

                                el.evaluate("""
                                    node => {
                                        node.style.border = '3px solid red';
                                        node.style.backgroundColor = 'rgba(255,0,0,0.1)';
                                    }
                                """)

                                img_path = os.path.join(
                                    self.evidence_dir,
                                    f"evidence_{session_id}_{count}.png"
                                )

                                page.screenshot(path=img_path)

                                el.evaluate("""
                                    node => {
                                        node.style.border = '';
                                        node.style.backgroundColor = '';
                                    }
                                """)

                                findings.append({
                                    "text": text,
                                    "reason": res['reason'],
                                    "link": url,
                                    "image": img_path
                                })

                                count += 1

                        except:
                            continue

            except Exception as e:
                print(f"⚠️ Fatal error: {e}")

            finally:
                try:
                    browser.close()
                except:
                    pass

        return findings



'''from playwright.sync_api import sync_playwright
import time
import os
import json
import re
from datetime import datetime


class EnterpriseScraper:
    def __init__(self):
        self.base_dir = os.getcwd()
        self.evidence_dir = os.path.join(self.base_dir, "evidence")
        if not os.path.exists(self.evidence_dir):
            os.makedirs(self.evidence_dir)

    # ---------------------------------------------------------
    # Cookie Loader
    # ---------------------------------------------------------
    def load_cookies(self, context):
        cookie_file = "cookies.json"
        if os.path.exists(cookie_file):
            try:
                with open(cookie_file, 'r') as f:
                    cookies = json.load(f)
                    for c in cookies:
                        if 'sameSite' in c and c['sameSite'] not in ["Strict", "Lax", "None"]:
                            c['sameSite'] = "None"
                    context.add_cookies(cookies)
                print("🍪 Session Cookies Injected.")
                return True
            except Exception as e:
                print("⚠️ Cookie load failed:", e)
        return False

    # ---------------------------------------------------------
    # Text Cleaner
    # ---------------------------------------------------------
    def clean_text(self, text):
        lines = text.split('\n')
        valid_lines = []
        garbage = [
            "Reply", "See translation", "View all",
            "Log in", "Sign up", "Liked by",
            "View more", "Hide", "View hidden comments", # Added to ignore button text
            "View replies"
        ]

        for line in lines:
            l = line.strip()
            if re.match(r'^\d+[hmwd]$', l):
                continue
            if "likes" in l and len(l) < 15:
                continue
            if len(l) < 2:
                continue
            if any(g in l for g in garbage):
                continue
            valid_lines.append(l)

        if not valid_lines:
            return None

        return " ".join(valid_lines)

    # ---------------------------------------------------------
    # SCROLL LOGIC (KEPT AS REQUESTED)
    # ---------------------------------------------------------
    def perform_continuous_scroll(self, page, presses=4):
        """
        Your original PageDown scroll logic.
        """
        try:
            # Ensure page focus (Safe corner click)
            page.mouse.click(10, 10)
            time.sleep(0.2)

            for _ in range(presses):
                page.keyboard.press("PageDown")
                time.sleep(0.4) 

            return True
        except Exception as e:
            print(f"⚠️ Scroll error: {e}")
            return False

    # ---------------------------------------------------------
    # HIDDEN CONTENT REVEALER (UPGRADED)
    # ---------------------------------------------------------
    def expand_threads(self, page):
        """
        Specifically targets 'View hidden comments' to find toxic content.
        """
        try:
            # 1. Target Hidden Comments (The most important one for you)
            # We use a specific locator to avoid clicking profiles
            hidden_btns = page.locator("div[role='button']:has-text('View hidden comments')").all()
            
            for btn in hidden_btns:
                if btn.is_visible():
                    try:
                        # Scroll slightly to make sure it's in view
                        btn.scroll_into_view_if_needed()
                        # Force click in case it's covered by a 'tooltip'
                        btn.click(force=True)
                        # Small wait to let the hidden words like 'chutiya' load
                        time.sleep(0.5)
                    except: pass

            # 2. Target Replies (Optional, limited to first 3 to save time)
            reply_btns = page.locator("div[role='button']:has-text('View replies')").all()
            for i, btn in enumerate(reply_btns):
                if i > 3: break
                if btn.is_visible():
                    try:
                        btn.scroll_into_view_if_needed()
                        btn.click(force=True)
                        time.sleep(0.2)
                    except: pass
            
            # NOTE: Removed the generic "more" clicker as it causes random profile clicks.

        except:
            pass

    # ---------------------------------------------------------
    # MAIN RUN
    # ---------------------------------------------------------
    def run(self, url, max_limit, analyzer):
        findings = []
        count = 0
        seen_comments = set()
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        with sync_playwright() as p:
            print("🚀 Launching Scraper...")

            iphone = p.devices['iPhone 13 Pro'].copy()
            iphone['viewport'] = {'width': 390, 'height': 844}

            browser = p.chromium.launch(
                headless=False,
                channel="msedge",
                args=["--disable-blink-features=AutomationControlled"]
            )

            context = browser.new_context(**iphone)
            self.load_cookies(context)
            page = context.new_page()

            try:
                print(f"🌍 Opening: {url}")
                page.goto(url, timeout=60000)
                time.sleep(6)

                stuck_counter = 0
                last_count = 0

                while count < max_limit:
                    if page.is_closed():
                        break

                    # 1. SCROLL (As requested)
                    self.perform_continuous_scroll(page, presses=4)

                    # 2. REVEAL HIDDEN CONTENT
                    self.expand_threads(page)
                    
                    # Wait a moment for hidden text to render
                    time.sleep(1.0)

                    comment_elements = page.locator(
                        "ul > li, div[role='button']"
                    ).all()

                    if len(comment_elements) == last_count:
                        stuck_counter += 1
                        if stuck_counter > 15:
                            print("✅ End of comments detected.")
                            break
                    else:
                        stuck_counter = 0

                    last_count = len(comment_elements)

                    batch = (
                        comment_elements[-30:]
                        if len(comment_elements) > 30
                        else comment_elements
                    )

                    for el in batch:
                        if count >= max_limit:
                            break
                        try:
                            raw_text = el.inner_text()
                            text = self.clean_text(raw_text)
                            if not text:
                                continue
                            if text in seen_comments:
                                continue

                            seen_comments.add(text)

                            res = analyzer.scan(text)
                            if res['is_toxic']:
                                print(f"🚨 MATCH: {text[:40]}... [{res['reason']}]")

                                el.scroll_into_view_if_needed()

                                el.evaluate("""
                                    node => {
                                        node.style.border = '3px solid red';
                                        node.style.backgroundColor = 'rgba(255,0,0,0.1)';
                                    }
                                """)

                                img_path = os.path.join(
                                    self.evidence_dir,
                                    f"evidence_{session_id}_{count}.png"
                                )

                                page.screenshot(path=img_path)

                                el.evaluate("""
                                    node => {
                                        node.style.border = '';
                                        node.style.backgroundColor = '';
                                    }
                                """)

                                findings.append({
                                    "text": text,
                                    "reason": res['reason'],
                                    "link": url,
                                    "image": img_path
                                })

                                count += 1

                        except:
                            continue

            except Exception as e:
                print(f"⚠️ Fatal error: {e}")

            finally:
                try:
                    browser.close()
                except:
                    pass

        return findings'''