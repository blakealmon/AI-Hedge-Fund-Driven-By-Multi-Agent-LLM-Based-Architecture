require("dotenv").config();

const fs = require("fs");
const path = require("path");

function formatDate(date) {
    return `${date.getMonth() + 1}/${date.getDate()}/${date.getFullYear()}`;
}

const API_KEY = process.env.PERPLEXITY_API_KEY;
const API_URL = "https://api.perplexity.ai/chat/completions";

async function fetchMacroNews(dateStr) {
    const payload = {
        model: "sonar-reasoning",
        messages: [
            {
                role: "system",
                content: "You are a helpful trading assistant."
            },
            {
                role: "user",
                content: `Can you search global or macroeconomics news for ${dateStr} that would be informative for trading / backtesting purposes? Only include news posted on this date and seven days prior.`
            }
        ],
        search_after_date_filter: formatDate(new Date(new Date(dateStr).setDate(new Date(dateStr).getDate() - 7))),
        search_before_date_filter: formatDate(new Date(new Date(dateStr).setDate(new Date(dateStr).getDate() + 1))),
        web_search_options: {
            search_context_size: "high",
            user_location: {
                country: "US",
            }
        }
    };

    const res = await fetch(API_URL, {
        method: "POST",
        headers: {
            "Authorization": `Bearer ${API_KEY}`,
            "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
    });

    if (!res.ok) {
        // log body
        const body = await res.text();
        console.error(`[Perplexity] Error fetching macro news for ${dateStr}: ${res.status} ${res.statusText}\n${body}`);
    }
    return await res.json();
}

async function main() {
    const today = new Date().toISOString().slice(0, 10);
    console.log(`[Perplexity] Fetching macro news for ${today}...`);
    try {
        const result = await fetchMacroNews(today);
        // Extract the main content and remove any thinking text (in HTML <think> tags)
        const rawContent = result.choices[0].message.content;
        result.cleanedOutput = rawContent.replace(/<think>[\s\S]*?<\/think>/g, '')
            .trim();
        const outputDir = path.join(__dirname, "perplexity_macro_news");
        if (!fs.existsSync(outputDir)) {
            fs.mkdirSync(outputDir, { recursive: true });
        }
        const outFile = path.join(outputDir, `macro_news_${today}.json`);
        fs.writeFileSync(outFile, JSON.stringify(result, null, 2));
        console.log(`[Perplexity] Saved news for ${today} to ${outFile}`);
    } catch (e) {
        console.error(`[Perplexity] Error for ${today}: ${e.message}`);
    }
}

main();