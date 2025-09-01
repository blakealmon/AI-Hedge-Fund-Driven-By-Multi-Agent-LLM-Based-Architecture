// tools/dataflow_fixtures/scrape_wallstreetbets.js
// Node.js script to fetch top posts from r/wallstreetbets for a range of dates and a stock ticker using fetch API
// Usage: node scrape_wallstreetbets.js YYYY-MM-DD YYYY-MM-DD TICKER

const fs = require('fs');
const path = require('path');

const ticker_to_company = {
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "GOOGL": "Google",
    "AMZN": "Amazon",
    "TSLA": "Tesla",
    "NVDA": "Nvidia",
    "TSM": "Taiwan Semiconductor Manufacturing Company OR TSMC",
    "JPM": "JPMorgan Chase OR JP Morgan",
    "JNJ": "Johnson & Johnson OR JNJ",
    "V": "Visa",
    "WMT": "Walmart",
    "META": "Meta OR Facebook",
    "AMD": "AMD",
    "INTC": "Intel",
    "QCOM": "Qualcomm",
    "BABA": "Alibaba",
    "ADBE": "Adobe",
    "NFLX": "Netflix",
    "CRM": "Salesforce",
    "PYPL": "PayPal",
    "PLTR": "Palantir",
    "MU": "Micron",
    "SQ": "Block OR Square",
    "ZM": "Zoom",
    "CSCO": "Cisco",
    "SHOP": "Shopify",
    "ORCL": "Oracle",
    "X": "Twitter OR X",
    "SPOT": "Spotify",
    "AVGO": "Broadcom",
    "ASML": "ASML ",
    "TWLO": "Twilio",
    "SNAP": "Snap Inc.",
    "TEAM": "Atlassian",
    "SQSP": "Squarespace",
    "UBER": "Uber",
    "ROKU": "Roku",
    "PINS": "Pinterest",
};

async function fetchRedditJSON(subreddit, after = null, limit = 100) {
    // This function now takes a query string and after token
    // subreddit is always 'wallstreetbets' here
    let url = `https://www.reddit.com/r/${subreddit}/search.json?q=${encodeURIComponent(after.q)}&limit=${after.limit || 100}&sort=new&restrict_sr=1`;
    if (after.after) url += `&after=${after.after}`;
    const res = await fetch(url, {
        headers: { 'User-Agent': 'node:abmr-fixture:v1.0' }
    });
    // Log rate limit headers
    const ratelimitRemaining = res.headers.get('x-ratelimit-remaining');
    const ratelimitReset = res.headers.get('x-ratelimit-reset');
    const ratelimitUsed = res.headers.get('x-ratelimit-used');
    console.log(`[Reddit API] Ratelimit-Remaining: ${ratelimitRemaining}, Ratelimit-Reset: ${ratelimitReset}, Ratelimit-Used: ${ratelimitUsed}`);
    if (ratelimitRemaining !== null && Number(ratelimitRemaining) <= 1) {
        const waitSec = ratelimitReset ? Number(ratelimitReset) : 60;
        console.log(`[Reddit API] Approaching rate limit, waiting for ${waitSec} seconds...`);
        await new Promise(resolve => setTimeout(resolve, waitSec * 1000));
    }
    if (!res.ok) throw new Error(`Failed to fetch: ${res.status}`);
    return await res.json();
}

function toFixture(post) {
    return {
        title: post.title,
        content: post.selftext || '',
        url: `https://reddit.com${post.permalink}`,
        upvotes: post.ups,
        posted_date: new Date(post.created_utc * 1000).toISOString().slice(0, 10),
        created_utc: post.created_utc,
        id: post.id,
        selftext: post.selftext || '',
        score: post.score,
        num_comments: post.num_comments,
    };
}

function dateRange(start, end) {
    const arr = [];
    let dt = new Date(start);
    const endDt = new Date(end);
    while (dt <= endDt) {
        arr.push(dt.toISOString().slice(0, 10));
        dt.setDate(dt.getDate() + 1);
    }
    return arr;
}

async function scrapeWallstreetBetsRange(startDate, ticker, outDir) {
    let allPosts = [];
    let keepGoing = true;
    // Get company names to search for
    let companyNames = [];
    if (ticker_to_company[ticker]) {
        companyNames = ticker_to_company[ticker].split('OR').map(n => n.trim());
    } else {
        companyNames = [ticker]; // fallback to ticker if not found
    }
    console.log(`[WallstreetBets] Fetching posts for ${ticker} (${companyNames.join(', ')}) until ${startDate}`);
    let mergedPosts = [];
    for (const name of companyNames) {
        let after = null;
        let foundThisBatch = 0;
        let reachedStartDate = false;
        let postsForName = [];
        while (keepGoing && !reachedStartDate) {
            try {
                const json = await fetchRedditJSON('wallstreetbets', {q: name, after, limit: 100});
                const posts = json.data.children.map(c => c.data);
                for (const post of posts) {
                    const postDate = new Date(post.created_utc * 1000).toISOString().slice(0, 10);
                    postsForName.push(toFixture(post));
                    foundThisBatch++;
                    if (postDate <= startDate) {
                        reachedStartDate = true;
                        break;
                    }
                }
                console.log(`[WallstreetBets] Found ${foundThisBatch} posts for query '${name}' in this batch, total so far: ${postsForName.length}`);
                after = json.data.after;
                if (!after) break;
                // Add a small delay between requests to avoid hammering the API
                await new Promise(resolve => setTimeout(resolve, 100));
            } catch (err) {
                console.error(`[WallstreetBets] Error fetching posts for query '${name}': ${err}`);
                break;
            }
        }
        mergedPosts = mergedPosts.concat(postsForName);
    }
    // Merge and sort by created_utc
    mergedPosts.sort((a, b) => b.created_utc - a.created_utc);
    const outFile = path.join(outDir, `wallstreetbets_${ticker}_${startDate}_${new Date().toISOString().slice(0, 10)}.json`);
    fs.writeFileSync(outFile, JSON.stringify(mergedPosts, null, 2));
    console.log(`[WallstreetBets] Wrote ${mergedPosts.length} posts to ${outFile}`);
}

// Usage: node scrape_wallstreetbets.js 2025-07-18 AAPL
if (require.main === module) {
    const [startDate] = process.argv.slice(2);
    if (!startDate) {
        console.error('Usage: node scrape_wallstreetbets.js YYYY-MM-DD');
        process.exit(1);
    }
    const repoRoot = path.resolve(__dirname);
    const outDir = path.join(repoRoot, 'reddit_data');
    if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });
    // Loop over every ticker in ticker_to_company
    (async () => {
        for (const ticker of Object.keys(ticker_to_company)) {
            await scrapeWallstreetBetsRange(startDate, ticker, outDir);
        }
    })();
}
