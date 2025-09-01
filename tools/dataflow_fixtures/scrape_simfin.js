require("dotenv").config();

const path = require("path");
const fs = require("fs");

const outputDir = path.join(__dirname, "simfin_data");

// Helper function for sleeping
const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

// Array of tickers to process
const tickers = ["AMZN", "META", "AAPL", "NVDA", "GOOG"];

// Main async function to process tickers sequentially
async function processTickersSequentially() {
    for (const ticker of tickers) {
        const res = await fetch(
            `https://backend.simfin.com/api/v3/companies/statements/verbose?ticker=${ticker}&statements=PL,BS,CF&start=2015-01-01&ttm=true`,
            {
                method: "GET",
                headers: {
                    accept: "application/json",
                    Authorization: `${process.env.SIMFIN_API_KEY}`,
                },
            }
        ).then((res) => res.json());
        
        // Sleep for 1 second after each fetch to avoid rate limiting
        await sleep(1000);

        if (res) {
            console.log(res);
            res.forEach((item) => {
                item.statements.forEach((statement) => {
                    const statementType = statement.statement;
                    const statementData = statement.data;
                    statementData.forEach((indivStatement) => {
                        const statementYear = indivStatement["Fiscal Year"];
                        const statementQuarter = indivStatement["Fiscal Period"];

                        const outFile = path.join(
                            outputDir,
                            `${ticker}_${statementType}_${statementYear}_${statementQuarter}.json`
                        );
                        if (!fs.existsSync(outputDir)) {
                            fs.mkdirSync(outputDir, { recursive: true });
                        }

                        fs.writeFileSync(outFile, JSON.stringify(statementData, null, 2));
                    });
                });
            });
        }
    }
}

// Call the function to start processing
processTickersSequentially();
