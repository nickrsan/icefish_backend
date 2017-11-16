ICEFISH_INIT = false;
ICEFISH_GRAPH_SYNC=false;
ICEFISH_UPDATE_INTERVAL = 90;  // how often to check for updates of data
ICEFISH_QUERY_ROOT_URL = "/api/ctd/";

icefish_charts = {};
icefish_data_records = [];


function unpack(rows, key) {
    return rows.map(function(row) { return row[key]; });
}

function set_up_events(graphs_object){
    // Primarily handles keeping graph X axes in sync
    console.log("Setting up events");
    graphs = Object.keys(graphs_object).map(function(graph){ return graphs_object[graph].div;});  // basically a list comprehension to get all of the graph divs
    graphs.forEach(function(graph) {
        console.log("Setting up for single graph");
        console.log(graph);
        graph.on("plotly_relayout", function(ranges){
            // this function will handle relaying out all of the other graphs once we change the X scale on any one of them.
            // The first bit of code is used to make sure that we don't go into infinite recursion (this triggers on "relayout"
            // which we need to also call on each graph once we make changes to it, so we need to keep track of if we're still
            // responding to the first relayout call. So, we track that with ICEFISH_GRAPH_SYNC. Then, we create an end_sync
            // function which fires on the Plotly.relayout Promise completion, which just subtracts from the number of
            // graphs we're still *expecting* to be relaid out and sets ICEFISH_GRAPH_SYNC to false if we get to 0 graphs remaining.
            // That way, it can respond to any future relayout calls again.

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
                if(graph === other_graph || !ICEFISH_INIT){ return } // don't process the same graph
                var update = {'xaxis.range': [ranges["xaxis.range[0]"], ranges["xaxis.range[1]"]]};
                Plotly.relayout(other_graph, update).then(end_sync, end_sync);
            });

        });
        graph.on("plotly_autoscale", function(){});
    });
}

function get_initial_data(divs) {
    // divs should be a dictionary that has keys "temperature", "pressure", and "salinity, with values corresponding
    // to the IDs of the elements to put those charts into
    console.log("In function");
    $.ajax({
        url: ICEFISH_QUERY_ROOT_URL,
        success: function (data, status, xhr) {
            console.log("In success, plotting");
            icefish_data_records = data;  // sorted desc, so keep track of it so we can request newer ones later

            var temperature = document.getElementById(divs["temperature"]);
            var pressure = document.getElementById(divs["pressure"]);
            var salinity = document.getElementById(divs["salinity"]);

            var temperature_layout = {
                xaxis: {title: 'Time'},
                yaxis: {title: 'Temperature'}, //range:[-1.92, -1.905]},
                margin: {t: 20},
                hovermode: 'closest'
            };
            a = Plotly.plot(temperature, [{
                    x: unpack(data, "dt").reverse(),  // we have to reverse them all so we can connect new additions later
                    y: unpack(data, "temp").reverse(),
                    name: "Temperature (C)"
                }, {
                    x: unpack(data, "dt").reverse(),
                    y: unpack(data, "freezing_point").reverse(),
                    name: "Freezing Point"
                }

                ],
                temperature_layout
            );

            var pressure_layout = {
                xaxis: {title: 'Time'},
                yaxis: {title: 'Pressure'}, // range:[18.7,19]},
                margin: {t: 20},
                hovermode: 'closest'
            };
            Plotly.plot(pressure, [{
                    x: unpack(data, "dt").reverse(),
                    y: unpack(data, "pressure").reverse(),
                }],
                pressure_layout
            );

            var salinity_layout = {
                xaxis: {title: 'Time'},
                yaxis: {title: 'Salinity'}, //range:[34.62,34.66]},
                margin: {t: 20},
                hovermode: 'closest'
            };
            var a = Plotly.plot(salinity, [{
                    x: unpack(data, "dt").reverse(),
                    y: unpack(data, "salinity").reverse(),
                    line: {color: "#FF6600"},
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

    check_for_updates = setInterval(function(){
        console.log("Checking for update since " + icefish_data_records[0].dt );
        $.ajax({
            url: ICEFISH_QUERY_ROOT_URL + "?since=" + icefish_data_records[0].dt,
            success: function (data, status, xhr) {
                if (data.length == 0){ return } // no update available

                console.log("Retrieved update");
                // Plotly.extendTraces(icefish_charts["temperature"], {x:unpack(data, "temp")});
                extend_chart(data, icefish_charts.temperature, 0);
                extend_chart(data, icefish_charts.temperature, 1, "freezing_point");
                extend_chart(data, icefish_charts.pressure, 0);
                extend_chart(data, icefish_charts.salinity, 0);

                icefish_data_records = data.concat(icefish_data_records);  // again, keep this data for the *next* time we run this
                                                                            // concat at the end so that if the above fails, it tries again later
            },
            error: function (data, status, xhr) {
                oonsole.log("UPDATE ERROR");
            },
        });
    }, ICEFISH_UPDATE_INTERVAL*1000); // schedule the update so it happens every interval seconds)
    console.log("Function complete");
}

function extend_chart(new_records, variable, index, variable_name){
    if (variable_name === undefined){ // this lets us override it for multitrace charts like temperature
        variable_name = variable.variable_name
    }
    var new_x = unpack(new_records, "dt").reverse();
    var new_y = unpack(new_records, variable_name).reverse();  // we have to reverse it so it correctly attaches the graph items in order
    for(var i=0;i<new_x.length;i++) {
        Plotly.extendTraces(variable.div_name, {x:[[new_x[i]]], y:[[new_y[i]]]}, [index]);
    }
}