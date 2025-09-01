// tools/dataflow_fixtures/scrape_finnhub.js
// Node.js script to fetch and save finnhub data for a ticker using the finnhub npm module
// Usage: node scrape_finnhub.js TICKER API_KEY OUT_DIR

const fs = require("fs");
const path = require("path");
const finnhub = require("finnhub");

const DATA_TYPES = [
  "insider_trans",
  "SEC_filings",
  "news_data",
  "insider_senti",
  "fin_as_reported",
];

async function fetchAndSaveFinnhubData(
  ticker,
  apiKey,
  outDir,
  startDate,
  endDate,
  windowLabel
) {
  const finnhubClient = new finnhub.DefaultApi(apiKey);

  // Helper for ratelimit retry
  async function callWithRateLimit(fn) {
    while (true) {
      try {
        return await fn();
      } catch (err) {
        if (err && err.error && err.error.includes("API limit reached.")) {
          console.warn("Finnhub API limit reached. Sleeping for 10 seconds...");
          await new Promise((res) => setTimeout(res, 10000));
        } else {
          throw err;
        }
      }
    }
  }

  // insider_trans
  const insiderTransPath = path.join(outDir, "finnhub_data", "insider_trans", `${windowLabel}.json`);
  if (fs.existsSync(insiderTransPath)) {
    console.log(`Skipped insider_trans (exists): ${insiderTransPath}`);
  } else {
    let insiderTrans = await callWithRateLimit(
      () =>
        new Promise((resolve, reject) => {
          finnhubClient.insiderTransactions(
            ticker,
            { from: startDate, to: endDate },
            (err, data) => {
              if (err) reject(err);
              else resolve(data);
            }
          );
        })
    );
    fs.writeFileSync(insiderTransPath, JSON.stringify(insiderTrans, null, 2));
    console.log("Saved insider_trans");
  }

  // SEC_filings
  const secFilingsPath = path.join(outDir, "finnhub_data", "SEC_filings", `${windowLabel}.json`);
  if (fs.existsSync(secFilingsPath)) {
    console.log(`Skipped SEC_filings (exists): ${secFilingsPath}`);
  } else {
    let secFilings = await callWithRateLimit(
      () =>
        new Promise((resolve, reject) => {
          finnhubClient.filings(
            { symbol: ticker, from: startDate, to: endDate },
            (err, data) => {
              if (err) reject(err);
              else resolve(data);
            }
          );
        })
    );
    fs.writeFileSync(secFilingsPath, JSON.stringify(secFilings, null, 2));
    console.log("Saved SEC_filings");
  }

  // news_data
  const newsDataPath = path.join(outDir, "finnhub_data", "news_data", `${windowLabel}.json`);
  if (fs.existsSync(newsDataPath)) {
    console.log(`Skipped news_data (exists): ${newsDataPath}`);
  } else {
    let newsData = await callWithRateLimit(
      () =>
        new Promise((resolve, reject) => {
          finnhubClient.companyNews(ticker, startDate, endDate, (err, data) => {
            if (err) reject(err);
            else resolve(data);
          });
        })
    );
    fs.writeFileSync(newsDataPath, JSON.stringify(newsData, null, 2));
    console.log("Saved news_data");
  }

  // insider_senti
  const insiderSentiPath = path.join(outDir, "finnhub_data", "insider_senti", `${windowLabel}.json`);
  if (fs.existsSync(insiderSentiPath)) {
    console.log(`Skipped insider_senti (exists): ${insiderSentiPath}`);
  } else {
    let insiderSenti = await callWithRateLimit(
      () =>
        new Promise((resolve, reject) => {
          finnhubClient.insiderSentiment(
            ticker,
            startDate,
            endDate,
            (err, data) => {
              if (err) reject(err);
              else resolve(data);
            }
          );
        })
    );
    fs.writeFileSync(insiderSentiPath, JSON.stringify(insiderSenti, null, 2));
    console.log("Saved insider_senti");
  }

  // fin_as_reported (annual and quarterly)
  for (const period of ["annual", "quarterly"]) {
    let periodStartDate;
    const endDt = new Date(endDate);
    if (period === "annual") {
      const startDt = new Date(endDt);
      startDt.setFullYear(endDt.getFullYear() - 1);
      periodStartDate = startDt.toISOString().slice(0, 10);
    } else if (period === "quarterly") {
      const startDt = new Date(endDt);
      startDt.setMonth(endDt.getMonth() - 3);
      periodStartDate = startDt.toISOString().slice(0, 10);
    }
    // Check for existing destination file first (skip fetch if exists)
    const reportDir = path.join(outDir, "finnhub_data", "fin_as_reported");
    const destPathForWindow = path.join(reportDir, `${windowLabel}_${period}.json`);
    if (fs.existsSync(destPathForWindow)) {
      console.log(`Skipped fin_as_reported (${period}) — destination exists: ${destPathForWindow}`);
      continue;
    }
    // Check for existing cached file within a month
    const files = fs.readdirSync(reportDir);
    let foundRecent = false;
    let targetDate = new Date(endDate);
    for (const file of files) {
      const match = file.match(
        new RegExp(
          `^${ticker}_(\\d{4}-\\d{2}-\\d{2})_\\d{4}-\\d{2}-\\d{2}_${period}\\.json$`
        )
      );
      if (match) {
        const fileDate = new Date(match[1]);
        const diffDays = Math.abs(
          (targetDate - fileDate) / (1000 * 60 * 60 * 24)
        );
        if (diffDays <= 31) {
          // Copy file contents only if destination doesn't exist
          const srcPath = path.join(reportDir, file);
          const destPath = path.join(reportDir, `${windowLabel}_${period}.json`);
          if (fs.existsSync(destPath)) {
            console.log(`Skipped copying cached fin_as_reported (${period}) — destination exists: ${destPath}`);
          } else {
            fs.copyFileSync(srcPath, destPath);
            console.log(`Copied cached fin_as_reported (${period}) from ${file}`);
          }
          foundRecent = true;
          break;
        }
      }
    }
    if (!foundRecent) {
      let asReported = await callWithRateLimit(
        () =>
          new Promise((resolve, reject) => {
            finnhubClient.financialsReported(
              {
                symbol: ticker,
                freq: period,
                from: periodStartDate,
                to: endDate,
              },
              (err, data) => {
                if (err) reject(err);
                else resolve(data);
              }
            );
          })
      );
      // Use acceptedDate from the first report in data (if available)
      let acceptedDate = null;
      if (
        asReported &&
        asReported.data &&
        asReported.data.length > 0 &&
        asReported.data[0].acceptedDate
      ) {
        acceptedDate = asReported.data[0].acceptedDate.split(" ")[0]; // YYYY-MM-DD
      } else {
        acceptedDate = endDate;
      }
      const outFileName = `${ticker}_${acceptedDate}_${period}.json`;
      const outFilePath = path.join(outDir, "finnhub_data", "fin_as_reported", outFileName);
      if (fs.existsSync(outFilePath)) {
        console.log(`Skipped fin_as_reported (${period}) — file exists: ${outFilePath}`);
      } else {
        fs.writeFileSync(outFilePath, JSON.stringify(asReported, null, 2));
        console.log(`Saved fin_as_reported (${period}) as ${outFileName}`);
      }
    }
  }
}

if (require.main === module) {
  const ticker_to_company = {
    AAPL: "Apple",
    MSFT: "Microsoft",
    GOOGL: "Google",
    AMZN: "Amazon",
    TSLA: "Tesla",
    NVDA: "Nvidia",
    TSM: "Taiwan Semiconductor Manufacturing Company OR TSMC",
    JPM: "JPMorgan Chase OR JP Morgan",
    JNJ: "Johnson & Johnson OR JNJ",
    V: "Visa",
    WMT: "Walmart",
    META: "Meta OR Facebook",
    AMD: "AMD",
    INTC: "Intel",
    QCOM: "Qualcomm",
    BABA: "Alibaba",
    ADBE: "Adobe",
    NFLX: "Netflix",
    CRM: "Salesforce",
    PYPL: "PayPal",
    PLTR: "Palantir",
    MU: "Micron",
    SQ: "Block OR Square",
    ZM: "Zoom",
    CSCO: "Cisco",
    SHOP: "Shopify",
    ORCL: "Oracle",
    SPOT: "Spotify",
    AVGO: "Broadcom",
    ASML: "ASML ",
    TWLO: "Twilio",
    SNAP: "Snap Inc.",
    TEAM: "Atlassian",
    SQSP: "Squarespace",
    UBER: "Uber",
    ROKU: "Roku",
    PINS: "Pinterest",
  };
  const [apiKey, outDir, startDate, endDate] = process.argv.slice(2);
  if (!apiKey || !outDir || !startDate || !endDate) {
    console.error(
      "Usage: node scrape_finnhub.js API_KEY OUT_DIR START_DATE END_DATE"
    );
    process.exit(1);
  }
  // Ensure output directories exist
  for (const type of DATA_TYPES) {
    const dir = path.join(outDir, "finnhub_data", type);
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  }
  // Helper to get all dates in range
  function getDateRange(start, end) {
    const arr = [];
    let dt = new Date(start);
    const endDt = new Date(end);
    while (dt <= endDt) {
      arr.push(dt.toISOString().slice(0, 10));
      dt.setDate(dt.getDate() + 1);
    }
    return arr;
  }

  const dateList = getDateRange(startDate, endDate);
  (async () => {
    for (const ticker of Object.keys(ticker_to_company)) {
      for (const date of dateList) {
        // Calculate 7 days before
        const endDt = new Date(date);
        const startDt = new Date(endDt);
        startDt.setDate(endDt.getDate() - 6); // 7 days window (inclusive)
        const sevenDaysBefore = startDt.toISOString().slice(0, 10);
        const windowLabel = `${ticker}_${sevenDaysBefore}_${date}`;
        await fetchAndSaveFinnhubData(
          ticker,
          apiKey,
          outDir,
          sevenDaysBefore,
          date,
          windowLabel
        ).catch((err) => {
          console.error(
            `Error fetching/saving finnhub data for ${ticker} ${sevenDaysBefore} to ${date}:`,
            err
          );
        });
      }
    }
  })();
}
