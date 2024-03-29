const puppeteer = require("puppeteer");

(async () => {
  const htmlFilename = await process.argv[2];
  const pdfFilename = await process.argv[3];
  const browser = await puppeteer.launch({
    args: [
      "--disable-gpu",
      "--no-sandbox",
      "--disable-setuid-sandbox",
      "--allow-file-access-from-files"
    ]
  });
  const page = await browser.newPage();
  page.on("console", (...args) => console.info("PAGE LOG:", ...args));
  page.on("error", err => {
    console.error(`Error event emitted: ${err}`);
    console.error(err.stack);
  });
  await page.emulateMedia("screen");
  await page.goto("file://" + htmlFilename, { waitUntil: "networkidle0" });
  await page.pdf({ path: pdfFilename, format: "A4" });
  await browser.close();
})();
