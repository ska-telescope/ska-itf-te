// This script fetches test execution data from XRay and populates a Google Sheet with the results.
// For setting up the CONFIG object, use environment variables stored in your local PrivateRules.mak file

const CONFIG = {
  JIRA_BASE_URL: "https://jira.skatelescope.org",
  USERNAME: environment.get("JIRA_USERNAME"), // Your Jira username (DC setup)
  API_TOKEN: environment.get("JIRA_API_TOKEN"), // Personal Access Token (DC setup)
  TEST_KEY: "XTP-104311",
  PAGE_SIZE: 50
};

function runXrayExtraction() {
  const sheet = getOrCreateSheet("XRay Imports");
  
  // 1. Manage Headers and get existing keys
  let existingKeys = {};
  if (sheet.getLastRow() === 0) {
    const baseHeaders = [
      "Execution Key", "Execution Date", "Status", "Is Pass", 
      "Cumulative Pass", "Execution #", "Pass Rate", "DISH_IDS Value", "DISH_IDS Count"
    ];
    sheet.appendRow(baseHeaders);
  } else {
    // Read Column A to find keys we already processed in earlier runs
    const totalRows = sheet.getLastRow();
    // Start at row 2 to bypass the text header
    if (totalRows > 1) {
      const columnAValues = sheet.getRange(2, 1, totalRows - 1, 1).getValues();
      columnAValues.forEach(row => {
        if (row[0]) existingKeys[row[0].toString().trim()] = true;
      });
    }
  }

  Logger.log("Starting incremental Xray extraction process...");
  const runs = getTestRuns(CONFIG.TEST_KEY);
  Logger.log(`Found a total of ${runs.length} runs in Jira.`);
  
  // 2. Filter out items already saved in the sheet
  const newRuns = runs.filter(run => {
    const key = run.testExecKey ? run.testExecKey.toString().trim() : "";
    return !existingKeys[key];
  });

  Logger.log(`Filtered out duplicates. Found ${newRuns.length} new runs to process.`);
  
  if (newRuns.length === 0) {
    Logger.log("Sheet is completely up to date. No API calls or writes needed.");
    return; 
  }

  // 3. Track historical variables for running metrics
  let cumulativePass = 0;
  let totalHistoricalExecutions = 0;

  if (sheet.getLastRow() > 1) {
    // Pull metadata tracking points from the absolute last row currently in the sheet
    const lastRowIdx = sheet.getLastRow();
    cumulativePass = parseInt(sheet.getRange(lastRowIdx, 5).getValue(), 10) || 0;
    totalHistoricalExecutions = parseInt(sheet.getRange(lastRowIdx, 6).getValue(), 10) || 0;
  }
  
  const rowsToAppend = [];
  let maxStepsFound = 0; 

  // Process only the new runs delta
  newRuns.forEach((run, index) => {
    const execNumber = totalHistoricalExecutions + index + 1;
    Logger.log(`[Processing New Run ${index + 1}/${newRuns.length}] Run Key: ${run.testExecKey}`);

    const status = run.status;
    const isPass = status === "PASS" ? 1 : 0;
    cumulativePass += isPass;
    const passRate = cumulativePass / execNumber;

    let dishIdsValue = "";
    let dishIdsCount = 0;
    const stepContents = [];

    try {
      // API call is ONLY executed for genuinely new runs
      const detailedRunData = getDetailedTestRun(run.id);
      
      if (detailedRunData && detailedRunData.steps && detailedRunData.steps.length > 0) {
        const totalSteps = detailedRunData.steps.length;
        if (totalSteps > maxStepsFound) {
          maxStepsFound = totalSteps; 
        }

        detailedRunData.steps.forEach((step, stepIdx) => {
          const rawResultObj = step.actual || step.actualResult || "";
          let cleanText = "";

          if (rawResultObj && typeof rawResultObj === 'object') {
            cleanText = rawResultObj.raw || rawResultObj.rendered || "";
          } else {
            cleanText = String(rawResultObj);
          }
          
          cleanText = cleanText.trim();
          stepContents.push(cleanText);

          if (cleanText.includes("DISH_IDS")) {
            const match = cleanText.match(/DISH_IDS\s*[:=]\s*["']?([^"\']+)["']?/i);
            if (match && match[1]) {
              dishIdsValue = match[1].trim();
              const idArray = dishIdsValue.split(/\s+/).filter(id => id.length > 0);
              dishIdsCount = idArray.length;
              Logger.log(`-> Found DISH_IDS at Step ${stepIdx + 1}: "${dishIdsValue}" (Count: ${dishIdsCount})`);
            }
          }
        });
      }
    } catch (e) {
      Logger.log(`-> ERROR extracting steps for Run ID ${run.id}: ${e.message}`);
    }

    // Construct the formula string dynamically
    const jiraUrl = `${CONFIG.JIRA_BASE_URL}/browse/${run.testExecKey}`;
    const hyperlinkFormula = `=HYPERLINK("${jiraUrl}", "${run.testExecKey}")`;

    // Push to array for bulk insertion (much faster)
    rowsToAppend.push([
      hyperlinkFormula,
      run.startedOn,
      status,
      isPass,
      cumulativePass,
      execNumber,
      passRate
    ]);

    rowsToAppend.push(baseRow.concat(stepContents));
  });

  if (rowsToAppend.length > 0) {
    const startRow = sheet.getLastRow() + 1;
    const currentHeadersCount = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0].length;
    
    // Dynamically expand headers horizontally if a new run has more steps than prior histories
    const totalColumnsNeeded = 9 + maxStepsFound;
    if (totalColumnsNeeded > currentHeadersCount) {
      const addedHeaders = [];
      for (let i = (currentHeadersCount - 9) + 1; i <= maxStepsFound; i++) {
        addedHeaders.push(`Step ${i} Content`);
      }
      sheet.getRange(1, currentHeadersCount + 1, 1, addedHeaders.length).setValues([addedHeaders]);
    }

    const standardWidth = sheet.getLastColumn();
    const normalizedRows = rowsToAppend.map(row => {
      while (row.length < standardWidth) {
        row.push(""); 
      }
      return row.slice(0, standardWidth); // Crop edge cases cleanly
    });

    Logger.log(`Appending ${normalizedRows.length} incremental rows to Google Sheet starting at row ${startRow}...`);
    sheet.getRange(startRow, 1, normalizedRows.length, standardWidth).setValues(normalizedRows);
    Logger.log("Incremental execution completed successfully.");
  }
}

function getTestRuns(testKey) {
  const url = `${CONFIG.JIRA_BASE_URL}/rest/raven/1.0/api/test/${testKey}/testruns`;
  return JSON.parse(jiraGet(url));
}

function getDetailedTestRun(testRunId) {
  const url = `${CONFIG.JIRA_BASE_URL}/rest/raven/1.0/api/testrun/${testRunId}`;
  return JSON.parse(jiraGet(url));
}

function jiraGet(url) {
  const options = {
    method: "get",
    headers: {
      "Authorization": "Bearer " + CONFIG.API_TOKEN,
      "Accept": "application/json"
    }
  };
  const response = UrlFetchApp.fetch(url, options);
  if (response.getResponseCode() !== 200) {
    throw new Error(response.getContentText());
  }
  return response.getContentText();
}

function getOrCreateSheet(name) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(name);
  if (!sheet) {
    sheet = ss.insertSheet(name);
  }
  return sheet;
}
