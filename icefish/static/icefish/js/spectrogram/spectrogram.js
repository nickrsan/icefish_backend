// Copyright (c) 2017 Ocean Sonics. All rights reserved.
// Dependency: jQuery, Flot, Chroma
// -----------------------------------------------------
// Constants
// =========
RAW_DATA_MIN=0;
RAW_DATA_MAX=255;
TICKSIZE_LEVEL=[3,6,10,12,20,30];
REF_LIMIT=60;
PORT=51675;
START_BIN=8;//Start of min/max calc
END_BIN=400;
HYDROPHONE_BASE_URL = "b195-moo-router.usap.gov";

// Controls
var $SELECT_STEP=$("#step")
var $INPUT_REF=$("#ref")
var $INPUT_VIEW=$("#view")
var $BUTTON_GO=$("#gobtn")

// sample size settings
FFT_CACHE_SIZE=2400;// = 10 min * 60 sec/min * 4 samps/sec
SPECTRUM_PLOTS=10;

// ticks settings
INTENSITY_DIVS=5;

// Color Pickers
// =============
// fade from light green to dark blue to black
var spectrumColor=chroma.scale(['#00ff00','#000044','#000000'],[0,0.5,1]).out("hex");
// lucy waterfall color scheme
var waterfallColor=chroma.scale(['#000000','#0000ff','#00ff00','#ffff00','#ff8000','#ff0000'],[0.0,0.2,0.4,0.6,0.8,1.0]).out("hex");
var numBins=410;
var numTicks=8;
var specBW=410/1024;

function UpdateGrid(sampRate)
{
	if(sampRate>32000)
	{
		numBins=400;
		numTicks=10;
	}
	else if(sampRate>8000)
	{
		numBins=416;
		numTicks=13;
	}
	else
	{
		numBins=410;
		numTicks=8;
	}
	specBW=numBins/1024;
}

// FFT Data Class
// ==============
function FFTData(fftRawData)
{
	// binary data parser
	var parser=new DataView(fftRawData);

	// Properties - parse from raw data
	this.sequence=parser.getUint16(0,true);
	this.length=parser.getUint16(2,true);
	this.refValue=-parser.getUint8(4,true)-120;
	this.sampleRate=parser.getUint32(5,true);
	this.phoneSensitivity=parser.getInt16(9,true);
	this.type=parser.getUint16(11,true);
	this.typeParam=[parser.getUint16(13,true),parser.getUint16(15,true),parser.getUint16(17,true),parser.getUint16(19,true)];

	UpdateGrid(this.sampleRate);

	// analyze the samples per second - inverse of FFT data rate
	// Note: refer to "icListen Command and Control Telemetry"
	switch(this.type)
	{
		case 4:
		case 5:
			this.samplesPerSecond=this.sampleRate/this.typeParam[0]/this.typeParam[2];
			break;
		case 6:
			this.samplesPerSecond=this.sampleRate/this.typeParam[1]/this.typeParam[2];
	}

	// calculate and save configuration for sample rate if not available
	if(!FFTData.configMap[this.sampleRate])
	{
		// calculate the configuration to temp variable
		var _allowMin=RAW_DATA_MIN/2+this.refValue-this.phoneSensitivity;
		var _allowMax=RAW_DATA_MAX/2+this.refValue-this.phoneSensitivity;
		var tickSize=this.sampleRate*specBW/numBins;
		var _ticks=[0];
		for(var i=1;i<numBins;i++)
			_ticks[i]=_ticks[i-1]+tickSize;

		// write to cache
		FFTData.configMap[this.sampleRate]={};
		FFTData.configMap[this.sampleRate].allowMin=_allowMin;
		FFTData.configMap[this.sampleRate].allowMax=_allowMax;
		FFTData.configMap[this.sampleRate].ticks=_ticks;
	}

	// use configuration for sample rate
	with(FFTData.configMap[this.sampleRate])
	{
		this.allowMin=allowMin;
		this.allowMax=allowMax;
		this.ticks=ticks;
	}

	// initialize min and max value
	this.min=Infinity;
	this.max=-Infinity;

	// Data
	this.data=[];
	for(var i=0;i<numBins;i++)
	{
		// process the row data and add to the sample data
		var point=parser.getUint8(21+i)/2+this.refValue-this.phoneSensitivity;

		// cut off the value to the allow range
		if(point<this.allowMin)
			point=this.allowMin;
		if(point>this.allowMax)
			point=this.allowMax;

		// push the processed data in to the sample
		this.data.push(point);

		// Only calculate the max/min after the filtered section.
		if((i>=START_BIN)&&(i<=END_BIN))
		{
			// re-calculate the maximum and minimum value for this sample
			if(point<this.min)
				this.min=point;
			if(point>this.max)
				this.max=point;
		}
	}
}
// static configuration map - for saving data rate specific configuration
FFTData.configMap={};


// FFT DataSet Class
// =================
function FFTDataSet(length)
{
	// Properties
	this.size=0;//actual size of data
	this.head=0;//head of circular array

	this.waterfallSize=0;

	this.currentSampleRate="N/A";
	this.currentRefValue="N/A";
	this.currentPhoneSensitivity="N/A";
	this.currentSamplesPerSecond="N/A";
	this.currentTicks="N/A";

	this.autoScale=false; //wether we want auto scale
	this.displayRef="N/A"; //reference for display
	this.displayTickSize="N/A" //tick size for display
	this.displayUpperBound="N/A" //opposite side of reference for display

	this.min=0;
	this.max=1;

	//Data
	this.samples=new Array(length);
}
FFTDataSet.prototype=
{
	//Method
	getSample:function(index)
	{
		//get sample in real position in circular array
		return this.samples[(this.samples.length+this.head-index)%this.samples.length];
	},
	add:function(fftData)
	{
		//reset on configuration changes
		if(fftData.sampleRate!=this.currentSampleRate
			|| fftData.refValue!=this.currentRefValue
			|| fftData.phoneSensitivity!=this.currentPhoneSensitivity
			|| fftData.samplesPerSecond!=this.currentSamplesPerSecond)
		{
			this.currentSampleRate=fftData.sampleRate;
			this.currentRefValue=fftData.refValue;
			this.currentPhoneSensitivity=fftData.phoneSensitivity;
			this.currentSamplesPerSecond=fftData.samplesPerSecond;

			this.currentTicks=fftData.ticks;

			//clear data
			this.size=0;
			this.head=0;
		}

		//update sample size and append data
		if(this.size<this.samples.length)
		{
			this.size++;
		}
		this.head=(this.head+1)%this.samples.length;
		this.samples[this.head]=fftData;

		//calculate the actual display size
		var displaySize=SPECTRUM_PLOTS>this.waterfallSize?SPECTRUM_PLOTS:this.waterfallSize;

		if(this.size<displaySize)
		{
			displaySize=this.size;
		}

		//re-calculate the max and min points
		var newMin=Infinity;
		var newMax=-Infinity;
		for(var i=displaySize-1;i>=0;i--)
		{
			sample=this.getSample(i);
			if(sample.min<newMin)
			{
				newMin=sample.min;
			}
			if(sample.max>newMax)
			{
				newMax=sample.max;
			}
		}
		this.min=newMin;
		this.max=newMax;

		//do auto scale if enabled
		if(this.autoScale)
		{
			this.doAutoScale();
		}
	},
	doAutoScale:function()
	{
		//get actual range and set default tick size to largest tick level
		var range=(this.max-this.min)/INTENSITY_DIVS;
		var level=TICKSIZE_LEVEL.length-1;
		var tickSize, ref,upperBound;

		//attempt to find the best match for the tick level
		for(var i=0;i<TICKSIZE_LEVEL.length;i++)
		{
			if(TICKSIZE_LEVEL[i]>=range)
			{
				level=i;
				break;
			}
		}

		do
		{
			//set the tick size to current level
			tickSize=TICKSIZE_LEVEL[level];
			//truncate the min value
			ref=Math.floor(this.min/tickSize)*tickSize;
			//get the max value by skip INTENSITY_DIVS ticks
			upperBound=ref+INTENSITY_DIVS*tickSize;

			//try to fit the graph into next tick level
			level++;
		}while(upperBound<this.max);

		//apply new scale to display setting
		$SELECT_STEP.val(tickSize);
		$INPUT_REF.val(ref);
		UpdateDisplaySetting();
	}
}

// FFT Spectrum Class
// ==================
function FFTSpectrum($spectrum,dataSet)
{
	//Bind
	this.$=$spectrum;//bind html element
	this.dataSet=dataSet;//bind data set

	//Properties
	this.options=
	{
		grid:
		{
			color:"#FFF",
			backgroundColor:"#000",
			margin:{right:24}
		},
		xaxis:
		{
			show:true,
			min:0,
			labelHeight:24
		},
		yaxis:
		{
			show:true,
			labelWidth:48
		}
	}
	this.displayData=[];
}
FFTSpectrum.prototype=
{
	//Method
	update:function()
	{
		var source=this.dataSet;

		//always change chart options
		with(this.options)
		{
			xaxis.max=source.currentSampleRate*specBW;
			xaxis.tickSize=Math.floor(source.currentSampleRate*specBW/numTicks);

			yaxis.min=source.displayRef;
			yaxis.max=source.displayUpperBound;
			yaxis.tickSize=source.displayTickSize;
		}

		//limit the number to SPECTRUM_PLOTS or the data available
		var spectrumSize=source.size<SPECTRUM_PLOTS?source.size:SPECTRUM_PLOTS;

		//prepare ticks for display data.
		var ticks=source.currentTicks;

		//prepare data to be displayed
		this.displayData=[];
		for(var i=spectrumSize-1;i>=0;i--)
		{
			//map the values to points
			var samplePoints=source.getSample(i).data.map(function(value,index)
			{
				return [ticks[index],value];
			});
			//push to display data
			this.displayData.push(
			{
				data:samplePoints,
				color:spectrumColor(i/SPECTRUM_PLOTS)
			});
		}

		//replot it!
		this.replot();
	},
	replot:function()
	{
		this.plot=$.plot(this.$,this.displayData,this.options);
	}
}

// FFT Waterfall Class
// ===================
function FFTWaterfall($waterfall,dataSet,view)
{
	// Bind
	this.$=$waterfall;//bind html element
	this.dataSet=dataSet;//bind data set
	this.view=undefined==view?parseFloat($INPUT_VIEW.val()):view;

	//Properties
	var self=this;
	this.options=
	{
		grid:
		{
			color:"#FFF",
			margin:{right:24}
		},
		xaxis:
		{
			show:true,
			labelHeight:24,
			tickDecimals:1
		},
		yaxis:
		{
			show:true,
			labelWidth:48,
			min:0,
			tickLength:0
		},
		hooks:
		{
			drawBackground:function(plot,canvasContext)
			{
				//wrapper function to make the caller
				//the instance of FFTWaterfall
				self.drawSpectrum(plot,canvasContext);
			}
		},
		waterfall:{ref:0}
	}

	//setup canvas buffer
	this.bufCanvas=document.createElement("canvas");
	this.bufContext=this.bufCanvas.getContext("2d");
	this.bufCanvas.height=numBins;

	//setup move canvas
	this.movCanvas=document.createElement("canvas");
	this.movContext=this.movCanvas.getContext("2d");
	this.movCanvas.height=numBins;
}
FFTWaterfall.prototype=
{
	// Methods
	// NOTE: this is a hook callback function for drawBackground() of flot.js
	drawSpectrum:function(plot,canvasContext)
	{
		var source=this.dataSet;

		//update waterfall data size
		source.waterfallSize=Math.ceil(this.view*60*this.dataSet.currentSamplesPerSecond);

		//get waterfall plot options
		var options=plot.getOptions().waterfall;

		//get plot offset
		var offset=plot.getPlotOffset();
		offset.width=waterfallDisplay.$.width()-offset.left-offset.right;
		offset.height=waterfallDisplay.$.height()-offset.top-offset.bottom;

		//prepare buffer
		this.bufCanvas.width=source.waterfallSize;
		this.bufContext.fillStyle="#000000";
		this.bufContext.fillRect(0,0,this.bufCanvas.width,this.bufCanvas.height);

		//limit the number to WATERFALL_SAMPLE_SIZE or the data available
		if(source.size<source.waterfallSize)
			source.waterfallSize=source.size;

		var range,ref;
		with(FFTData.configMap[source.currentSampleRate])
		{
			ref=source.displayRef;
			range=source.displayUpperBound-source.displayRef;
		}

		//detect option changes
		var optionsChanged=false;

		if(source.currentSampleRate!=this.lastSampleRate || source.displayRef!=this.lastRef || source.displayUpperBound!=this.lastUpperBound || source.displayTickSize!=this.lastTickSize || this.view!=this.lastView)
		{
			optionsChanged=true;

			//remember last options
			this.lastSampleRate=source.currentSampleRate;
			this.lastRef=source.displayRef;
			this.lastUpperBound=source.displayUpperBound;
			this.lastTickSize=source.displayTickSize;
			this.lastView=this.view;
			this.bufCanvas.height=numBins;
			this.movCanvas.height=numBins;
		}

		//fill data and render transformation
		var data;
		for(var i=0,x=this.bufCanvas.width-1;i<source.waterfallSize;i++,x--)
		{
			data=source.getSample(i).data;
			for(var j=0,y=this.bufCanvas.height-1;j<numBins;j++,y--)
			{
				this.bufContext.fillStyle=waterfallColor((data[j]-ref)/range);
				this.bufContext.fillRect(x,y,1,1);
			}
			if(!optionsChanged)
			{
				this.bufContext.drawImage(this.movCanvas,-1,0);
				break;
			}
		}

		//draw the display
		canvasContext.drawImage(this.bufCanvas,0,0,this.bufCanvas.width,this.bufCanvas.height,offset.left,offset.top,offset.width,offset.height);

		//save last image
		this.movCanvas.width=this.bufCanvas.width;
		this.movContext.drawImage(this.bufCanvas,0,0);
	},
	update:function()
	{
		var source=this.dataSet;

		//always change chart options
		with(this.options)
		{
			// update current time
			var currentTime=new Date().getTime()+timeOffset;
			$("[data-field=currentTime]").text(new Date(currentTime).toUTCString());
			var d=new Date(currentTime)||new Date();
			var minute=d.getMinutes();
			var second=d.getSeconds();
			var milliseconds=d.getMilliseconds();
			var currentTick=minute+second/60+milliseconds/60000;
			var totalLength=this.view;

			xaxis.min=currentTick-totalLength;
			xaxis.max=currentTick;
			xaxis.tickSize = totalLength/10;

			yaxis.max=source.currentSampleRate*specBW;
			yaxis.tickSize=Math.floor(source.currentSampleRate*specBW/numTicks);
		}
		//replot it!
		this.replot();
	},
	replot:function()
	{
		this.plot=$.plot(this.$,[],this.options);
	}
}

// Global Variable
// ===============
dataSet=new FFTDataSet(FFT_CACHE_SIZE);
spectrumGraph=null;
waterfallDisplay=null;
firstSamp=1;

// Initialize
// ==========
$(function()
{
	//Menu Builer Utility Functions
	var buildStepMenu=function()
	{
		//clear inner html of selector SELECT_STEP
		$SELECT_STEP.html("");

		//append options inside SELECT_STEP
		for(var i=0;i<TICKSIZE_LEVEL.length;i++)
		{
			$SELECT_STEP.append($("<option>").val(TICKSIZE_LEVEL[i]).text(TICKSIZE_LEVEL[i]+"dB"));
		}
	}

	//Initialize the websockets
	var url=document.URL;
	var ws;

	//establish connection
	ws=new WebSocket("ws://"+HYDROPHONE_BASE_URL+":"+PORT);

	//setup the websockets
	ws.isConnected=false;//use to test if the socket is closed on error
	ws.binaryType="arraybuffer";
	ws.onopen=function()
	{
		$SELECT_STEP.val(dataSet.displayTickSize);
		$INPUT_REF.val(dataSet.displayRef);

		//setup graph
		//spectrumGraph=new FFTSpectrum($("#spectrum-graph > .chart"),dataSet);
		waterfallDisplay=new FFTWaterfall($("#waterfall-display > .chart"),dataSet);

		//mark connect state to connected
		ws.isConnected=true;
	}
	ws.onerror=function()
	{
		//display error message
		$(".chartmessage").text("Error loading data...").show();
		ws.close();
		clearTimeout(t);
	}
	ws.onmessage=function(event)
	{
		//pre-processing data, get sample rate and bandwidth of current data
		var newData=new FFTData(event.data);
		var sampRate=(newData.sampleRate>32000)?newData.sampleRate*400/1024:newData.sampleRate*0.4;
		sampRate=sampRate>1000?sampRate=(sampRate/1000)+"kHz":sampRate+"Hz";

		dataSet.add(newData);
		if(firstSamp==1)
		{
			firstSamp=0;
			dataSet.doAutoScale();
			$(".chartmessage").text("").hide();
		}
		spectrumGraph.update();
		waterfallDisplay.update();

		$("[data-field=fftBandWidth]").text(sampRate);

		$("select").prop("disabled",false);
		$("input").prop("disabled",false);
		$("button").prop("disabled",false);
		$BUTTON_GO.html("Stop");
	}
	ws.onclose=function()
	{
		//display error message
		if(ws.isConnected)
		{
			$(".chartmessage").text("Data stream stopped unexpectedly...").show();
			ws.isConnected=false;
		}
		$BUTTON_GO.html("Restart");
	}

	//Initial the UI
	buildStepMenu();
	$SELECT_STEP.change(function()
	{
		UpdateDisplaySetting();
		$SELECT_STEP.blur();
	});
	$INPUT_REF.keyup(function(event)
	{
		switch(event.keyCode)
		{
			case 27:
				this.value=dataSet.displayRef;
			case 13:
				$INPUT_REF.blur();
				break;
		}
	});
	$INPUT_REF.blur(function(event)
	{
		UpdateDisplaySetting();
	});
	$INPUT_VIEW.keyup(function(event)
	{
		switch(event.keyCode)
		{
			case 27:
				this.value=waterfallDisplay.view;
			case 13:
				$INPUT_VIEW.blur();
				break;
		}
	});
	$INPUT_VIEW.blur(function(event)
	{
		UpdateDisplaySetting();
	});
	$("#rescale").click(function()
	{
		dataSet.doAutoScale();
	});
	$BUTTON_GO.click(function()
	{
		if(ws.isConnected)
		{
			ws.isConnected=false;
			ws.close();
		}
		else
		{
			document.location.reload(false);
		}
	});

	timeOffset = 780;
	
});

function UpdateDisplaySetting()
{
	var step=parseInt($SELECT_STEP.val());
	var ref=parseInt($INPUT_REF.val());
	var time=parseFloat($INPUT_VIEW.val());

	//validate type-in inputs and escape on failure
	if(isNaN(ref))
	{
		$INPUT_REF.val(dataSet.displayRef);
		return;
	}
	if(isNaN(time) || (time<=0))
	{
		$INPUT_VIEW.val(waterfallDisplay.view);
		return;
	}
	if((dataSet.displayRef==ref) && (dataSet.displayTickSize==step) && (waterfallDisplay.view==time))
	{
		return;
	}

	//set lowest intensity
	dataSet.displayRef=ref;
	$INPUT_REF.val(ref);

	//set step size
	dataSet.displayTickSize=step;
	$SELECT_STEP.val(step);

	//set time scale
	waterfallDisplay.view=time;
	$INPUT_VIEW.val(waterfallDisplay.view);

	dataSet.displayUpperBound=dataSet.displayRef+dataSet.displayTickSize*INTENSITY_DIVS;

	spectrumGraph.update();
	waterfallDisplay.replot();
	waterfallDisplay.replot();
}
