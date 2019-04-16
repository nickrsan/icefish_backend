const puppeteer = require('puppeteer');

//===Revision history===
//Current: refactored paths and times to variables, added logging, changed initial wait to 8s. Moved style injection to post-page load
//v1.1 uses 120 second delay to wait for data load 4/9/19 pc
//v 1.0 uses 90 second delay to wait for data load (results in some 4kb blue images) 4/5/19 pc


const { exec } = require('child_process');

async function run() {
	
	// an attempt to get the network drive mapped for this script - I've removed the username and password
	exec('net use \\192.168.0.42\photos', (err, stdout, stderr) => {
		  if (err) {
			  console.log("Failed to connect");
			// node couldn't execute the command
			return;
		  }

		  // the *entire* stdout and stderr (buffered)
		  console.log(`stdout: ${stdout}`);
		  console.log(`stderr: ${stderr}`);
		});  // map the network connection

	var output_path = 'file://192.168.0.42/photos/incoming/CTD_image/CTD_';
	var load_wait = 8000;   // ms - time to wait for all code to load on the page before changing the sizes
	var data_wait = 120000;  //ms - time to wait for data to load
	
	console.log("First run");
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
    await page.screenshot({ path: new URL(output_path + Date.now() + '.png'), clip: {x: 705.2, y: 0, width: 1049.6, height: 591} });
	await page.close();
	await browser.close();
	console.log("First run complete");
	
	//subsequent iterations with interval of 0.5 hour
	await setInterval (async function subsequent(){
		console.log("Taking new snapshot");
		let browser = await puppeteer.launch({ headless: true });
		let page = await browser.newPage();
		await page.setViewport({ width: 1804, height:591 });
		await page.goto('http://b195-moo-stream.usap.gov/kiosk/');
		await page.waitFor(load_wait); //wait for the page to load elements
		await page.addStyleTag({content: '.modebar { display: none !important; }'}); //hide the plotly toolbar, which is displayed by default since no mouse on this computer (assumes touchscreen)
		await page.addStyleTag({content: '.video_container { display: none !important }'}); //kill the video so error msg isn't overlaid
		await page.evaluate(() => { change_chart_size() }); //pop the charts to large size
		await page.waitFor(data_wait); //wait 120s for all data to load (90s previously, gave some issues?)
		await page.screenshot({ path: new URL(output_path + Date.now() + '.png'), clip: {x: 705.2, y: 0, width: 1049.6, height: 591} });
		await page.close();
		await browser.close();
		console.log("Snapshot complete");
	},1675000); //sets the wake up time interval (currently 0.5 hour, when you account for 5 and 120 second sleeps)

};

run();