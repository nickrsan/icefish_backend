const puppeteer = require('puppeteer');

//===Revision history===
//Current: added date string to console.log 4/18/19 pc
//v1.3 Got rid of nicks "new URL" in the output path and seems to run again. 
//v1.2 refactored paths and times to variables, added logging, changed initial wait to 8s. Moved style injection to post-page load (not working)
//v1.1 uses 120 second delay to wait for data load 4/9/19 pc
//v1.0 uses 90 second delay to wait for data load (results in some 4kb blue images) 4/5/19 pc


async function run() {
	
	var output_path = 'Y:/incoming/CTD_image/CTD_';
	var load_wait = 8000;   // ms - time to wait for all code to load on the page before changing the sizes (was orig. 5 s, but may have caused blue image issue. 
	var data_wait = 120000;  //ms - time to wait for data to load
	var cycle_time = 1672000;  //ms - cycle time, summing all three above values should give 30 minutes (1800000 ms)
	
	var dt = new Date(); //Calculate the timestamp (might need to use Date.now() to be compatible with browsers in the future)
	var utcDate = dt.toUTCString(); //convert the timestamp to UTC
 
	console.log("First run: " + utcDate);
	//console.log("First run");
	//initial iteration, image available about 95 seconds after executing
	let browser = await puppeteer.launch({ headless: true });
    let page = await browser.newPage();
    await page.setViewport({ width: 1804, height:591 });
    await page.goto('http://b195-moo-stream.usap.gov/kiosk/');
	await page.waitFor(load_wait); //wait for the page to load elements
	await page.addStyleTag({content: '.modebar { display: none !important; }'}); //hide the plotly toolbar, which is displayed by default since no mouse on this computer (assumes touchscreen)
	await page.addStyleTag({content: '.video_container { display: none !important }'}); //kill the video so error msg isn't overlaid
	await page.evaluate(() => { change_chart_size() }); //pop the charts to large size
	await page.waitFor(data_wait); //wait 120s for all data to load (90s previously, gave some issues?)
    await page.screenshot({ path: output_path + Date.now() + '.png', clip: {x: 705.2, y: 0, width: 1049.6, height: 591} });
	await page.close();
	await browser.close();
	console.log("First run complete");
	
	//subsequent iterations with interval of 0.5 hour
	
	await setInterval (async function subsequent(){
		var dt = new Date();
		var utcDate = dt.toUTCString();
 
		console.log("Taking new snapshot: " + utcDate);
		let browser = await puppeteer.launch({ headless: true });
		let page = await browser.newPage();
		await page.setViewport({ width: 1804, height:591 });
		await page.goto('http://b195-moo-stream.usap.gov/kiosk/');
		await page.waitFor(load_wait); //wait for the page to load elements
		await page.addStyleTag({content: '.modebar { display: none !important; }'}); //hide the plotly toolbar, which is displayed by default since no mouse on this computer (assumes touchscreen)
		await page.addStyleTag({content: '.video_container { display: none !important }'}); //kill the video so error msg isn't overlaid
		await page.evaluate(() => { change_chart_size() }); //pop the charts to large size
		await page.waitFor(data_wait); //wait 120s for all data to load (90s previously, gave some issues?)
		await page.screenshot({ path: output_path + Date.now() + '.png', clip: {x: 705.2, y: 0, width: 1049.6, height: 591} });
		await page.close();
		await browser.close();
		console.log("Snapshot complete");
	},cycle_time); //sets the wake up time interval (currently 0.5 hour, when you account for 8 and 120 second sleeps)

};

run();