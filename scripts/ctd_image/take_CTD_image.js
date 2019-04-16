const puppeteer = require('puppeteer');

//===Revision history===
//Current: v1.1 uses 120 second delay to wait for data load 4/9/19 pc
//v 1.0 uses 90 second delay to wait for data load (results in some 4kb blue images) 4/5/19 pc


async function run() {
	//initial iteration, image available about 95 seconds after executing
	let browser = await puppeteer.launch({ headless: true });
    let page = await browser.newPage();
    await page.setViewport({ width: 1804, height:591 });
    await page.goto('http://b195-moo-stream.usap.gov/kiosk/');
	await page.addStyleTag({content: '.modebar { display: none !important; }'}); //hide the plotly toolbar, which is displayed by default since no mouse on this computer (assumes touchscreen)
	await page.addStyleTag({content: '.video_container { display: none !important }'}); //kill the video so error msg isn't overlaid
	await page.waitFor(5000); //wait for the page to load elements
	await page.evaluate(() => { change_chart_size() }); //pop the charts to large size
	await page.waitFor(120000); //wait 120s for all data to load (90s previously, gave some issues?)
    await page.screenshot({ path: 'Y:/incoming/CTD_image/CTD_' + Date.now() + '.png', clip: {x: 705.2, y: 0, width: 1049.6, height: 591} });
	await page.close();
	await browser.close();
	
	//subsequent iterations with interval of 0.5 hour
	await setInterval (async function subsequent(){
		let browser = await puppeteer.launch({ headless: true });
		let page = await browser.newPage();
		await page.setViewport({ width: 1804, height:591 });
		await page.goto('http://b195-moo-stream.usap.gov/kiosk/');
		await page.addStyleTag({content: '.modebar { display: none !important; }'}); //hide the plotly toolbar, which is displayed by default since no mouse on this computer (assumes touchscreen)
		await page.addStyleTag({content: '.video_container { display: none !important }'}); //kill the video so error msg isn't overlaid
		await page.waitFor(5000); //wait for the page to load elements
		await page.evaluate(() => { change_chart_size() }); //pop the charts to large size
		await page.waitFor(120000); //wait 120s for all data to load (90s previously, gave some issues?)
		await page.screenshot({ path: 'Y:/incoming/CTD_image/CTD_' + Date.now() + '.png', clip: {x: 705.2, y: 0, width: 1049.6, height: 591} });
		await page.close();
		await browser.close();
	},1675000); //sets the wake up time interval (currenlty 0.5 hour, when you account for 5 and 120 second sleeps)

};

run();