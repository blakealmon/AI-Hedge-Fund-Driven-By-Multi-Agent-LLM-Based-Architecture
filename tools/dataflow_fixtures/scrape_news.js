// tools/dataflow_fixtures/scrape_news.js
// Node.js script to fetch top posts from r/news for a range of dates using fetch API
// Usage: node scrape_news.js YYYY-MM-DD YYYY-MM-DD

const fs = require('fs');
const path = require('path');

// Removed page cap: we now stream continuously until user aborts (Ctrl+C)
async function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function fetchListing(after=null, limit=100) {
  let url = `https://www.reddit.com/r/news/new.json?limit=${limit}&restrict_sr=1`;
  if (after) url += `&after=${after}`;
  const res = await fetch(url, { headers: { 'User-Agent': 'node:abmr-news-scraper:v1.0' } });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  // Light rate-limit pacing if remaining header low
  const remaining = res.headers.get('x-ratelimit-remaining');
  const reset = res.headers.get('x-ratelimit-reset');
  if (remaining !== null && Number(remaining) < 1) {
    const waitSec = reset ? Number(reset) : 60;
    console.log(`[RateLimit] Low remaining=${remaining}. Waiting ${waitSec}s`);
    await sleep(waitSec * 1000);
  }
  const json = await res.json();
  // Save raw response for debugging
  try {
    const debugDir = path.join(process.cwd(), 'debug_raw_news');
    if (!fs.existsSync(debugDir)) fs.mkdirSync(debugDir, { recursive: true });
    const ts = new Date().toISOString().replace(/[:.]/g, '-');
    const debugFile = path.join(debugDir, `raw_news_${ts}.json`);
    fs.writeFileSync(debugFile, JSON.stringify(json, null, 2));
  } catch (e) {
    console.error(`[debug] Failed to save raw news response: ${e.message}`);
  }
  return json;
}

function toFixture(post) {
  return {
    id: post.id,
    title: post.title,
    author: post.author,
    created_utc: post.created_utc,
    posted_date: new Date(post.created_utc * 1000).toISOString().slice(0,10),
    url: `https://reddit.com${post.permalink}`,
    external_url: post.url,
    domain: post.domain,
    score: post.score,
    upvotes: post.ups,
    num_comments: post.num_comments,
    over_18: post.over_18,
    stickied: post.stickied,
    locked: post.locked,
    spoiler: post.spoiler,
    removed_by_category: post.removed_by_category || null,
    selftext: post.selftext || '',
    flair: post.link_flair_text || null
  };
}

function parseDateArg(d) {
  if (!d) return null;
  if (!/^\d{4}-\d{2}-\d{2}$/.test(d)) {
    console.error(`Invalid date format '${d}'. Expected YYYY-MM-DD`);
    process.exit(1);
  }
  return d;
}

async function scrapeNews(stopDateStr=null) {
  let after = null;
  let page = 0;
  let all = [];
  let stopDate = stopDateStr ? new Date(stopDateStr) : null;
  console.log(`[news] Start continuous scraping. stopDate=${stopDateStr||'none'} (Ctrl+C to stop)`);

  while (true) {
    page++;
    console.log(`[news] Page ${page} starting (after=${after})`);
    let json;
    try {
      json = await fetchListing(after, 100);
    } catch (e) {
      console.error(`[news] Fetch error page ${page}: ${e.message}`);
      await sleep(10000); // wait then retry
      continue;
    }

    const children = json?.data?.children || [];
    if (children.length === 0) {
      console.log('[news] No posts returned. Sleeping 30s then retry.');
      await sleep(30000);
      continue;
    }
    for (const c of children) {
      const p = c.data;
      const postDateStr = new Date(p.created_utc * 1000).toISOString().slice(0,10);
      all.push(toFixture(p));
      if (stopDate && new Date(postDateStr) <= stopDate) {
        console.log(`[news] Reached stop date (${stopDateStr}) at post ${p.id}. Stopping.`);
        after = null; // force break outer loop
        break;
      }
    }
    after = json.data.after || json.data.children[json.data.children.length - 1]?.data?.name; // use last post's name if no after token
    console.log(after)
    // Compute newest & oldest dates reached so far
    if (all.length) {
      // Only compute once per page for performance
      const newest = new Date(Math.max(...all.map(p=>p.created_utc))*1000).toISOString().slice(0,10);
      const oldest = new Date(Math.min(...all.map(p=>p.created_utc))*1000).toISOString().slice(0,10);
      console.log(`[news] Page ${page} complete: total=${all.length} window=${oldest} -> ${newest} nextAfter=${after}`);
    } else {
      console.log(`[news] Page ${page} complete: no posts collected yet.`);
    }
    if (!after) {
      console.log('[news] No further pagination token. Sleeping 60s then continuing to poll for new posts.');
      await sleep(60000);
      continue;
    }
    // Incremental write after each page (snapshot)
    try {
      const today = new Date().toISOString().slice(0,10);
      const tag = stopDateStr ? stopDateStr : 'all';
      const outFile = path.join(process.cwd(), "reddit_news_data",`news_${tag}_${today}.json`);
      if (!fs.existsSync(path.dirname(outFile))) {
        fs.mkdirSync(path.dirname(outFile), { recursive: true });
      }
      fs.writeFileSync(outFile, JSON.stringify(all.sort((a,b)=> b.created_utc - a.created_utc), null, 2));
      console.log(`[news] Snapshot saved (${all.length} posts).`);
    } catch (e) {
      console.error(`[news] Snapshot write error: ${e.message}`);
    }
    await sleep(300); // throttle pacing
  }

}

if (require.main === module) {
  const [argDate] = process.argv.slice(2);
  const stopDate = parseDateArg(argDate);
  scrapeNews(stopDate);
}
