const { chromium } = require('playwright');
const { Readability } = require('@mozilla/readability');
const { JSDOM } = require('jsdom');
const TurndownService = require('turndown');

async function fetchContent(url) {
    let browser;
    try {
        browser = await chromium.launch({
            executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
            headless: true
        });
        const page = await browser.newPage();
        
        // Anti-bot evasions
        await page.addInitScript(() => {
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        });

        // Set realistic user agent
        await page.setExtraHTTPHeaders({
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
        });

        console.error(`Navigating to ${url}...`);
        await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });
        
        // Special wait for WeChat articles
        if (url.includes('mp.weixin.qq.com')) {
            await page.waitForTimeout(2000); // Give it time to render DOM
        }

        const html = await page.content();
        
        // Parse readability
        const dom = new JSDOM(html, { url });
        
        // Fix WeChat lazy loaded images
        const images = dom.window.document.querySelectorAll('img');
        images.forEach(img => {
            if (img.getAttribute('data-src')) {
                img.setAttribute('src', img.getAttribute('data-src'));
            }
        });

        const reader = new Readability(dom.window.document);
        const article = reader.parse();

        if (!article || !article.content) {
            console.error("Failed to parse article content. Raw HTML length:", html.length);
            console.log(html.substring(0, 500)); // Print partial for debugging
            process.exit(1);
        }

        // Convert to markdown
        const turndownService = new TurndownService({
            headingStyle: 'atx',
            codeBlockStyle: 'fenced'
        });
        
        const markdown = turndownService.turndown(article.content);
        
        const res = {
            url: url,
            title: article.title,
            content: markdown
        };
        
        // If JSON output requested
        if (process.argv.includes('--json')) {
            console.log(JSON.stringify(res, null, 2));
        } else {
            console.log(`# ${article.title}\n\n${markdown}`);
        }
        
    } catch (e) {
        console.error("Error fetching URL:", e);
        process.exit(1);
    } finally {
        if (browser) {
            await browser.close();
        }
    }
}

const url = process.argv[2];
if (!url) {
    console.error("Usage: node fetch.js <url> [--json]");
    process.exit(1);
}

fetchContent(url);
