// tools/dataflow_fixtures/scrape_worldnews.js
// Node.js script to fetch top posts from r/worldnews for a range of dates using fetch API
// Usage: node scrape_worldnews.js YYYY-MM-DD YYYY-MM-DD

const fs = require('fs');
const path = require('path');

// Removed page cap: we now stream continuously until user aborts (Ctrl+C)
async function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function fetchListing(after=null, limit=100) {
  let url = `https://www.reddit.com/r/worldnews/new.json?limit=${limit}&restrict_sr=1`;
  if (after) url += `&after=${after}`;
  const res = await fetch(url, { headers: { 'User-Agent': 'node:abmr-worldnews-scraper:v1.0' } });
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
    const debugDir = path.join(process.cwd(), 'debug_raw_worldnews');
    if (!fs.existsSync(debugDir)) fs.mkdirSync(debugDir, { recursive: true });
    const ts = new Date().toISOString().replace(/[:.]/g, '-');
    const debugFile = path.join(debugDir, `raw_worldnews_${ts}.json`);
    fs.writeFileSync(debugFile, JSON.stringify(json, null, 2));
  } catch (e) {
    console.error(`[debug] Failed to save raw worldnews response: ${e.message}`);
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

async function scrapeWorldNews(stopDateStr=null) {
  let after = null;
  let page = 0;
  let all = [];
  let stopDate = stopDateStr ? new Date(stopDateStr) : null;
  console.log(`[worldnews] Start continuous scraping. stopDate=${stopDateStr||'none'} (Ctrl+C to stop)`);

  while (true) {
    page++;
    let json;
    try {
      json = await fetchListing(after, 100);
    } catch (e) {
      console.error(`[worldnews] Fetch error page ${page}: ${e.message}`);
      break;
    }
    const children = json?.data?.children || [];
    if (children.length === 0) {
      console.log('[worldnews] No more posts.');
      break;
    }
    for (const c of children) {
      const p = c.data;
      const postDateStr = new Date(p.created_utc * 1000).toISOString().slice(0,10);
      all.push(toFixture(p));
      if (stopDate && new Date(postDateStr) <= stopDate) {
        console.log(`[worldnews] Reached stop date (${stopDateStr}) at post ${p.id}. Stopping.`);
        after = null; // force break outer loop
        break;
      }
    }
    after = json.data.after || json.data[-1]?.data?.name; // use last post's name if no after token
    // Compute newest & oldest dates reached so far
    if (all.length) {
      // Only compute once per page for performance
      const newest = new Date(Math.max(...all.map(p=>p.created_utc))*1000).toISOString().slice(0,10);
      const oldest = new Date(Math.min(...all.map(p=>p.created_utc))*1000).toISOString().slice(0,10);
      console.log(`[worldnews] Page ${page} complete: total=${all.length} window=${oldest} -> ${newest} nextAfter=${after}`);
    } else {
      console.log(`[worldnews] Page ${page} complete: no posts collected yet.`);
    }
    if (!after) {
      console.log('[worldnews] No further pagination token.');
      break;
    }
    // Incremental write after each page (snapshot)
    try {
      const today = new Date().toISOString().slice(0,10);
      const tag = stopDateStr ? stopDateStr : 'all';
      const outFile = path.join(process.cwd(), "reddit_worldnews_data",`worldnews_${tag}_${today}.json`);
      if (!fs.existsSync(path.dirname(outFile))) {
        fs.mkdirSync(path.dirname(outFile), { recursive: true });
      }
      fs.writeFileSync(outFile, JSON.stringify(all.sort((a,b)=> b.created_utc - a.created_utc), null, 2));
      console.log(`[worldnews] Snapshot saved (${all.length} posts).`);
    } catch (e) {
      console.error(`[worldnews] Snapshot write error: ${e.message}`);
    }
    await sleep(300); // throttle pacing
  }
}

if (require.main === module) {
  const [argDate] = process.argv.slice(2);
  const stopDate = parseDateArg(argDate);
  scrapeWorldNews(stopDate);
}
