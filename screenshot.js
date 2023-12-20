const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');

// Apply the stealth plugin to avoid detection
puppeteer.use(StealthPlugin());

// Get the URL from the command line arguments
const url = process.argv[2];
const timeout = 8000;

(async () => {
    // Launch the browser
    const browser = await puppeteer.launch({
        headless: true, // Assuming you want to run headless
    });

    // Open a new page
    const page = await browser.newPage();

    // Set the viewport for the page
    await page.setViewport({
        width: 1200,
        height: 2000,
        deviceScaleFactor: 1,
    });

	// Navigate to the URL
	await page.goto(url, {
		waitUntil: "networkidle0", // Wait for the network to be idle
		timeout: timeout,
	});


    // Take a screenshot after the page loads
    await page.screenshot({ 
        path: "screenshot.jpg",
        fullPage: false,
    });
    
    // Close the browser
    await browser.close();
})();
