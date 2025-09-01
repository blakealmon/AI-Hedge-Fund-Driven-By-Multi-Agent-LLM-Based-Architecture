require("dotenv").config();

const fs = require("fs");
const path = require("path");

// Helper function for sleeping
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

// Parse date range from command line
if (process.argv.length < 4) {
  console.error("Usage: node scrape_perplexity.js YYYY-MM-DD YYYY-MM-DD");
  process.exit(1);
}
const startDateStr = process.argv[2];
const endDateStr = process.argv[3];
const startDate = new Date(startDateStr);
const endDate = new Date(endDateStr);

function* dateRange(start, end) {
  let curr = new Date(start);
  while (curr <= end) {
    yield new Date(curr);
    curr.setDate(curr.getDate() + 1);
  }
}

function formatDate(date) {
    return `${date.getMonth() + 1}/${date.getDate()}/${date.getFullYear()}`;
}

const outputDir = path.join(__dirname, "perplexity_macro_news");
if (!fs.existsSync(outputDir)) {
  fs.mkdirSync(outputDir, { recursive: true });
}

const API_KEY = process.env.PERPLEXITY_API_KEY;
const API_URL = "https://api.perplexity.ai/chat/completions";

async function fetchMacroNews(dateStr) {
  const payload = {
    model: "sonar-reasoning",
    messages: [
      {
        role: "system",
        content: "You are a helpful trading assistant.",
      },
      {
        role: "user",
        content: `Can you search global or macroeconomics news for ${dateStr} that would be informative for trading / backtesting purposes? Only include news posted on this date and seven days prior.`,
      },
    ],
    search_after_date_filter: formatDate(
      new Date(new Date(dateStr).setDate(new Date(dateStr).getDate() - 7))
    ),
    search_before_date_filter: formatDate(
      new Date(new Date(dateStr).setDate(new Date(dateStr).getDate() + 1))
    ),
    web_search_options: {
      search_context_size: "high",
      user_location: {
        country: "US",
      },
    },
  };

  const res = await fetch(API_URL, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    throw new Error(`Perplexity API error: ${res.status} ${res.statusText}`);
  }
  return await res.json();
}

async function main() {
  for (const date of dateRange(startDate, endDate)) {
    const dateStr = date.toISOString().slice(0, 10);
    console.log(`[Perplexity] Fetching macro news for ${dateStr}...`);
    try {
      const outFile = path.join(outputDir, `macro_news_${dateStr}.json`);

      // Skip if file already exists
      if (fs.existsSync(outFile)) {
        console.log(
          `[Perplexity] File for ${dateStr} already exists, skipping.`
        );
        continue;
      }

      const result = await fetchMacroNews(dateStr);
      const rawContent = result.choices[0].message.content;
      result.cleanedOutput = rawContent
        .replace(/<think>[\s\S]*?<\/think>/g, "")
        .trim();
      fs.writeFileSync(outFile, JSON.stringify(result, null, 2));
      console.log(`[Perplexity] Saved news for ${dateStr} to ${outFile}`);
    } catch (e) {
      console.error(`[Perplexity] Error for ${dateStr}: ${e.message}`);
    }
    await sleep(2000); // Sleep 2 seconds between requests to avoid rate limits
  }
}

main();
