const { firefox } = require('playwright');
const fs = require('fs');
const actions = require('./actions.json');
require('dotenv').config();
let logs = [];
let page;


    (async () => {
            const args = Object.fromEntries(
                process.argv.slice(2).map(arg => arg.replace(/^--/, '').split('='))
            );

            const {coupon, domain, config, used_on_product_url} = args;

            if (!coupon || !domain) {
                error('❌ Missing required parameters: --coupon and --domain');
                log('Usage: node index.js --coupon=YOUR_COUPON --domain=YOUR_DOMAIN');
                return;
            }


            let siteConfig;
            try {
                siteConfig = config ? JSON.parse(config) : actions.sites?.[domain];
            } catch (e) {
                error(`❌ Invalid JSON in --config: ${e.message}`);
                return;
            }

            if (!siteConfig) {
                error(`❌ Domain "${domain}" not found in actions.json`);
                return;
            }


            if (typeof used_on_product_url === 'string') {
                siteConfig.productUrl = used_on_product_url;
            }

            const proxy = process.env.PROXY_SERVER
                ? {
                    server: process.env.PROXY_SERVER,
                    username: process.env.PROXY_USERNAME || undefined,
                    password: process.env.PROXY_PASSWORD || undefined
                }
                : undefined;


            log('[⏳] Starting headless-browser...');


            const browser = await firefox.launch({
                headless: true,
                ...(proxy && {proxy})
            });

            const context = await browser.newContext({
                userAgent:
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.5845.188 Safari/537.36',
                locale: 'en-US',
            });

            page = await context.newPage();


            // 🛡️ Anti-bot evasion
            await page.addInitScript(() => {
                Object.defineProperty(navigator, 'webdriver', {get: () => false});
                window.navigator.chrome = {runtime: {}};
                Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            });

            let couponIsValid = false;

            try {
                log(`[🌐] Go to Website ${siteConfig.productUrl}`);
                await page.goto(siteConfig.productUrl, {waitUntil: 'domcontentloaded', timeout: 60000});
                await page.waitForTimeout(siteConfig.waitTime);

                if (siteConfig.actions.length) {
                    for (let action of siteConfig.actions) {
                        log(`[👉] Action: ${action.name}`);
                        log(action.event);
                        if (action.selectors.length > 0) {
                            for (let selector of action.selectors) {
                                try {
                                    let issetSelector = await retryWaitForSelector(page, selector, {
                                        timeout: action.waitAfter,
                                        state: 'attached'
                                    }, 5, 1000, action.required);
                                    if (issetSelector) {
                                        if (action.type === 'fill') {
                                            await page.fill(selector, coupon, {timeout: action.waitAfter});
                                            await page.dispatchEvent(selector, 'input');
                                            await page.dispatchEvent(selector, 'change');
                                        } else if (action.type === 'click') {
                                            const el = await page.$(selector);
                                            if (el) {
                                                await el.evaluate(el => el.click()); // <- це "нативний" клік, як в браузері руками
                                            }
                                        } else {
                                            await page[action.type](selector, {timeout: action.waitAfter, force: true});
                                        }
                                        if (action.waitAfter) {
                                            log(`⏳ Waiting ${action.waitAfter}ms after action`);
                                            await new Promise(resolve => setTimeout(resolve, action.waitAfter));
                                        }
                                    }
                                } catch (e) {
                                    break;
                                    error(`[⚠️] Failed action "${action.name}" on selector "${selector}": ${e.message}`);
                                }
                            }
                        }
                    }
                }

                await page.waitForTimeout(siteConfig.waitTime);

                const element = await page.$(siteConfig.promoCode.elementAlert);
                if (element) {
                    const text = await element.innerText();
                    if (text.includes(siteConfig.promoCode.validText)) {
                        log('[🎉🎉🎉] Coupon is valid!');
                        couponIsValid = true;
                    } else {
                        log('[❌❌❌] Coupon is not valid.');
                    }
                } else {
                    log('[❌❌❌] Coupon is not valid.');
                }

            } catch (e) {
                error(`❌ Unexpected error: ${e.message}`);
            }
            const outputDir = './output';
            if (!fs.existsSync(outputDir)) {
                fs.mkdirSync(outputDir, {recursive: true});
            }
            const html = await page.content();
            await page.screenshot({path: `${outputDir}/screenshot.png`, fullPage: true});
            fs.writeFileSync(`${outputDir}/html_snapshot.html`, html);
            fs.writeFileSync(`${outputDir}/result.json`, JSON.stringify({logs, couponIsValid}, null, 2));
            await browser.close();
    })();

function log(message) {
    console.log(message);
    logs.push({ type: 'log', message, timestamp: new Date().toISOString() });
}

function error(message) {
    console.error(message);
    logs.push({ type: 'error', message, timestamp: new Date().toISOString() });
}

async function retryWaitForSelector(page, selector, options = {}, maxAttempts = 3, delayBetween = 1000, required = true) {
    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
        try {
            return await page.waitForSelector(selector, options);
        } catch (e) {
            log(`🔁 Attempt ${attempt} failed for selector "${selector}"`);
            if (attempt === maxAttempts || !required) {
                log(`Selector "${selector}" not found after ${maxAttempts} attempts.`);
                return false;
            }
            await new Promise(res => setTimeout(res, delayBetween));
        }
    }
}