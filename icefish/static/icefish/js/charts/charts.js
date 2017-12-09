ICEFISH_INIT = false;
ICEFISH_GRAPH_SYNC=false;
ICEFISH_UPDATE_INTERVAL = 60;  // how often to check for updates of data
ICEFISH_TESTING_ROOT_URL = "/api/ctd"; // "http://157.132.104.177:8009/api/ctd/"; // ?since=2017-11-13T22:00:00Z&before=2017-11-15T12:00:24Z"; //before=2017-11-15T12:00:24Z&
icefish_charts = {};
icefish_data_records = [];

chart_expanded = false;

open_dialog = null;  // if we open a dialog, store it here so we can close it

function unpack(rows, key) {
    return rows.map(function(row) { return row[key]; });
}

function synchronize_graphs(data){
    // this function will handle relaying out all of the other graphs once we change the X scale on any one of them.
    // The first bit of code is used to make sure that we don't go into infinite recursion (this triggers on "relayout"
    // which we need to also call on each graph once we make changes to it, so we need to keep track of if we're still
    // responding to the first relayout call. So, we track that with ICEFISH_GRAPH_SYNC. Then, we create an end_sync
    // function which fires on the Plotly.relayout Promise completion, which just subtracts from the number of
    // graphs we're still *expecting* to be relaid out and sets ICEFISH_GRAPH_SYNC to false if we get to 0 graphs remaining.
    // That way, it can respond to any future relayout calls again.

    console.log("Relayout triggered");
    var graph = data.graph;
    var graphs = data.graphs;
    var ranges = data.ranges;

    if (ICEFISH_GRAPH_SYNC === true){ return } // if we're already syncing graphs, stop, or else we'll trigger a cascade
    ICEFISH_GRAPH_SYNC=true;
    var items_to_layout = Object.keys(icefish_charts).length-1; // we won't flag the current item for relayout - happens on its own
    var end_sync = function() {
        items_to_layout--;
        if (items_to_layout === 0) {
            ICEFISH_GRAPH_SYNC = false;
        }
    };

    graphs.forEach(function(other_graph){
        // for all the other graphs, set their range to match the range on the update, then call Plotly.relayout to force the update
        if(graph === other_graph.div || !ICEFISH_INIT){ return } // don't process the same graph

        if (ranges["xaxis.autorange"] === undefined){ // basically, if the key isn't set to do an autorange, pull the specifics from the object, otherwise, just use the object for autoranging
            var update = {'xaxis.range': [ranges["xaxis.range[0]"], ranges["xaxis.range[1]"]]};
        }else{
            var update = ranges;
        }
        Plotly.relayout(other_graph.div, update).then(end_sync, end_sync);
    });

}

function set_up_events(graphs_object){
    // Primarily handles keeping graph X axes in sync
    console.log("Setting up events");
    graphs = Object.keys(graphs_object).map(function(graph){ return graphs_object[graph]});  // basically a list comprehension to get all of the graph divs
    graphs.forEach(function(graph) {
        console.log("Setting up for single graph");
        console.log(graph.div_name);
        graph.div.on("plotly_relayout", function(ranges){
            synchronize_graphs({graph: graph.div, graphs: graphs, ranges: ranges})
        });
        graph.div.on("plotly_autoscale", function(ranges){
            synchronize_graphs({graph: graph.div, graphs: graphs, ranges: ranges})
        });
    });

    window.onresize = function(){
        chart_autosize();
    }
}

function get_initial_data(divs) {
    // divs should be a dictionary that has keys "temperature", "pressure", and "salinity, with values corresponding
    // to the IDs of the elements to put those charts into
    console.log("In function");
    $.ajax({
        url: ICEFISH_TESTING_ROOT_URL,
        headers: {"Authorization": ICEFISH_CTD_API_TOKEN},
        success: function (data, status, xhr) {
            console.log("In success, plotting");
            icefish_data_records = data;  // sorted desc, so keep track of it so we can request newer ones later

            var temperature = document.getElementById(divs["temperature"]);
            var pressure = document.getElementById(divs["pressure"]);
            var salinity = document.getElementById(divs["salinity"]);

            var common_layout = {
                margin: {t: 10, b:50, l:50, r:0},
                hovermode: 'closest',
                plot_bgcolor: '#213c52',
                paper_bgcolor: '#213c52',
                showlegend: false,
                font: {color: "#ffffff"},
            };

            var temperature_layout = Object.assign({
                xaxis: {title: 'Time'},
                yaxis: {title: 'Temperature'},
            }, common_layout);  // merge the common layout items with the specific ones
            a = Plotly.plot(temperature, [
                {  // freezing point first because we want it to draw under temperature
                    x: unpack(data, "dt").reverse(),
                    y: unpack(data, "freezing_point").reverse(),
                    name: "Freezing Point",
                    line: {color: "#c3e9f4",},
                },
                {
                    x: unpack(data, "dt").reverse(),  // we have to reverse them all so we can connect new additions later
                    y: unpack(data, "temp").reverse(),
                    name: "Temperature (C)",
                    line: {color: "#3891ff",},
                },
                ],
                temperature_layout
            );

            var pressure_layout = Object.assign({
                xaxis: {title: 'Time'},
                yaxis: {title: 'Pressure'}
            }, common_layout);  // merge the common layout items with the specific ones
            Plotly.plot(pressure, [{
                    x: unpack(data, "dt").reverse(),
                    y: unpack(data, "pressure").reverse(),
                    line: {color: "#f10b7a"},
                }],
                pressure_layout
            );

            var salinity_layout = Object.assign({
                xaxis: {title: 'Time'},
                yaxis: {title: 'Salinity'}
            }, common_layout);  // merge the common layout items with the specific ones
            var a = Plotly.plot(salinity, [{
                    x: unpack(data, "dt").reverse(),
                    y: unpack(data, "salinity").reverse(),
                    line: {color: "#96e343"},
                }],
                salinity_layout
            );

            icefish_charts = {
                "temperature": {"div": temperature,
                                "layout": temperature_layout,
                                "div_name": divs["temperature"],
                                "variable_name": "temp",
                                },
                "salinity": {
                    "div": salinity,
                    "div_name": divs["salinity"],
                    "variable_name": "salinity",
                    "layout": salinity_layout,
                },
                "pressure": {
                    "div": pressure,
                    "div_name": divs["pressure"],
                    "variable_name": "pressure",
                    "layout": pressure_layout,
                }
            };

            set_up_events(icefish_charts);

            ICEFISH_INIT = true;
            console.log("Plotted!");
        },
        error: function (data, status, xhr) {
            console.log("error " + status);
        }
    });

    if(ICEFISH_REALTIME_CTD === true){ // if we *have* realtime CTD data on this server, schedule the update so it happens every interval seconds)
        check_for_updates = setInterval(update_charts, ICEFISH_UPDATE_INTERVAL*1000);
    }

    if (ICEFISH_HYDROPHONE_BASE_URL !== null){  // if we know where the spectrogram server is - this will be disabled for Internet version, so we want to check
        start_spectrogram();  // defined in CTD spectrogram library
    }

    //setTimeout(check_and_start_wowza, 5000);  // give the player a moment to be created, then tell it to play
    console.log("Function complete");
}

function check_and_start_wowza(){
    var player = WowzaPlayer.get('WowzaPlayerElement')
    if (!player.isPlaying()){
        player.play();
    }
}

function update_charts(){
    console.log("Checking for update since " + icefish_data_records[0].dt );
    $.ajax({
        url: ICEFISH_QUERY_ROOT_URL + "?since=" + icefish_data_records[0].dt,
        headers: {"Authorization": ICEFISH_CTD_API_TOKEN},
        success: function (data, status, xhr) {
            if (data.length == 0){ return } // no update available

            console.log("Retrieved update: " + data);
            // Plotly.extendTraces(icefish_charts["temperature"], {x:unpack(data, "temp")});
            extend_chart(data, icefish_charts.temperature, 0, "freezing_point");
            extend_chart(data, icefish_charts.temperature, 1);
            extend_chart(data, icefish_charts.pressure, 0);
            extend_chart(data, icefish_charts.salinity, 0);

            if(icefish_charts.temperature.layout.xaxis.range[1] == icefish_data_records[0].dt.replace("T", " ").replace("Z", "")) { // if they're currently viewing up through the newest record, then update their extent to include new ones. Replace T and Z in stored time data because the graph won't have that in the values
                var update = {'xaxis.range': [icefish_charts.temperature.layout.xaxis.range[0], data[0].dt]};
                Plotly.relayout(icefish_charts.temperature.div, update); // set the new range object and then update one of the charts - the other will follow because of events we've set up
            }

            icefish_data_records = data.concat(icefish_data_records);  // again, keep this data for the *next* time we run this
                                                                        // concat at the end so that if the above fails, it tries again later
        },
        error: function (data, status, xhr) {
            console.log("UPDATE ERROR");
        },
    });
}

function extend_chart(new_records, variable, index, variable_name){
    if (variable_name === undefined){ // this lets us override it for multitrace charts like temperature
        variable_name = variable.variable_name
    }

    var new_x = unpack(new_records, "dt").reverse();
    var new_y = unpack(new_records, variable_name).reverse();  // we have to reverse it so it correctly attaches the graph items in order
    for(var i=0;i<new_x.length;i++) {
        console.log("extending div " + variable.div_name + " with " + new_x[i] + " and " + new_y[i])
        Plotly.extendTraces(variable.div_name, {x:[[new_x[i]]], y:[[new_y[i]]]}, [index]);
    }
}

function chart_autorange(){
    /*
        Sends the autorange update to a single plot, causing all plots to update due to the event handlers we have set up.
     */
    Plotly.relayout(icefish_charts.temperature.div, {"xaxis.autorange": true, "yaxis.autorange": true})  // calling it on one will trigger it on all of them
}

function chart_autosize(){
    Object.keys(icefish_charts).forEach(function(chart){
        Plotly.Plots.resize(icefish_charts[chart].div).then(chart_autorange, chart_autorange);  // autorange on success or fail - only the last one will actually work - the rest will bail because the resizing is already in progress
    });
}

function change_chart_size(){
    //if (chart_expanded === false){
    $("#icefish_main").toggleClass("pure-u-md-17-24 pure-u-md-1-3");  // first is original, second is updated
    $("#icefish_charts").toggleClass("pure-md-1-4 pure-u-md-3-5");  // first is original, second is updated
    $("#icefish_chart_toggle_button").toggleClass("fa-caret-left fa-caret-right");  // first is original, second is updated
    //}

    chart_autosize();
}

function toggle_dialog(id, main_body_new_class){
    var transition = null;
    var toggle_main = null;
    if (open_dialog === null){  // there's nothing open already
        transition = "slide";
        open_dialog = id;
        toggle_main = true;
    }else if (open_dialog === id || (id === false && open_dialog !== null)){  // close *any* open dialogs if we pass in false and something is open
        transition = "slide";
        if (id === false){
            id = open_dialog;  // save it because we'll use it to close it
        }
        open_dialog = null;
        toggle_main = true;
    }else{  // something is open already, swap it
        $("#"+open_dialog).toggle();
        open_dialog = id;
        toggle_main = false; // don't do anything to the main divs if we're just swapping open panels
    }

    if (main_body_new_class === undefined){ // if it wasn't passed in, here's the default
        main_body_new_class = "pure-u-md-7-24"  // we pass it in for smaller panels
    }

    $("#"+id).toggle(transition);

    if (toggle_main === true){
        $("#icefish_main").toggleClass("pure-u-md-17-24 " + main_body_new_class);  // first is original, second is updated
        $("#icefish_charts").toggle();  // first is original, second is updated
    }
}