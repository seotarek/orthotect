import json
import urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

API_KEY = 'bb_live_sjZpgks0bH_J9ceecLEiXDFYius'

def create_session():
    req = urllib.request.Request(
        'https://api.browserbase.com/v1/sessions',
        data=b'{}',
        headers={
            'X-BB-API-Key': API_KEY,
            'Content-Type': 'application/json'
        }
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    print(f"Browserbase Session Created: {data['id']}")
    print(f"Recording URL: https://www.browserbase.com/sessions/{data['id']}")
    return data['connectUrl'], data['id']

def main():
    connect_url, session_id = create_session()
    out_dir = Path('docs/assets/screenshots')
    out_dir.mkdir(parents=True, exist_ok=True)
    
    styles_css = Path('docs/styles.css').read_text(encoding='utf-8')

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(connect_url)
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else context.new_page()
        page.set_viewport_size({'width': 1280, 'height': 800})
        
        # 1. Cyberpunk API Platform Hero
        cyber_html = Path('docs/templates/developer-api-platform-hero.html').read_text(encoding='utf-8')
        cyber_html = cyber_html.replace('<link rel="stylesheet" href="../styles.css">', f'<style>{styles_css}</style>')
        page.set_content(cyber_html, wait_until='networkidle')
        page.screenshot(path=str(out_dir / 'bb_cyber.png'))
        print('Captured: bb_cyber.png')

        # 2. Clinical Patient Intake Records
        clinical_html = Path('docs/templates/clinical-patient-intake-records.html').read_text(encoding='utf-8')
        clinical_html = clinical_html.replace('<link rel="stylesheet" href="../styles.css">', f'<style>{styles_css}</style>')
        page.set_content(clinical_html, wait_until='networkidle')
        page.screenshot(path=str(out_dir / 'bb_clinical.png'))
        print('Captured: bb_clinical.png')

        # 3. Live Homepage
        page.goto('https://seotarek.github.io/orthotect/', wait_until='networkidle')
        page.screenshot(path=str(out_dir / 'bb_home.png'))
        print('Captured: bb_home.png')

        # 4. Gallery Showcase
        page.goto('https://seotarek.github.io/orthotect/#gallery', wait_until='networkidle')
        page.wait_for_timeout(500)
        page.screenshot(path=str(out_dir / 'bb_gallery.png'))
        print('Captured: bb_gallery.png')

        browser.close()

    print(f"All Browserbase screenshots captured successfully in session {session_id}!")

if __name__ == '__main__':
    main()
