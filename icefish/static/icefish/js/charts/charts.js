INIT = false;
GRAPH_SYNC=false;

icefish_charts = [];

function unpack(rows, key) {
        return rows.map(function(row) { return row[key]; });
    }

    function set_up_events(graphs){
        // Primarily handles keeping graph X axes in sync
        console.log("Setting up events");
        graphs.forEach(function(graph) {
            console.log("Setting up for single graph");
            console.log(graph);
            graph.on("plotly_relayout", function(ranges){
                // this function will handle relaying out all of the other graphs once we change the X scale on any one of them.
                // The first bit of code is used to make sure that we don't go into infinite recursion (this triggers on "relayout"
                // which we need to also call on each graph once we make changes to it, so we need to keep track of if we're still
                // responding to the first relayout call. So, we track that with GRAPH_SYNC. Then, we create an end_sync
                // function which fires on the Plotly.relayout Promise completion, which just subtracts from the number of
                // graphs we're still *expecting* to be relaid out and sets GRAPH_SYNC to false if we get to 0 graphs remaining.
                // That way, it can respond to any future relayout calls again.

                if (GRAPH_SYNC === true){ return } // if we're already syncing graphs, stop, or else we'll trigger a cascade
                GRAPH_SYNC=true;
                var items_to_layout = icefish_charts.length-1; // we won't flag the current item for relayout - happens on its own
                var end_sync = function() {
                    items_to_layout--;
                    if (items_to_layout === 0) {
                        GRAPH_SYNC = false;
                    }
                };

                graphs.forEach(function(other_graph){
                    // for all the other graphs, set their range to match the range on the update, then call Plotly.relayout to force the update
                    if(graph === other_graph || !INIT){ return } // don't process the same graph
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
                url: "/api/ctd/",
                success: function (data, status, xhr) {
                    console.log("In success, plotting");
                    var temperature = document.getElementById(divs["temperature"]);
                    var pressure = document.getElementById(divs["pressure"]);
                    var salinity = document.getElementById(divs["salinity"]);

                    var temperature_layout ={
                            xaxis: {title: 'Time'},
                            yaxis: {title: 'Temperature'}, //range:[-1.92, -1.905]},
                            margin: {t: 20},
                            hovermode: 'closest'
                        };
                    a = Plotly.plot(temperature, [{
                            x: unpack(data, "dt"),
                            y: unpack(data, "temp"),
                            name: "Temperature (C)"
                        }, {x: unpack(data, "dt"),
                            y: unpack(data, "freezing_point"),
                            name: "Freezing Point"}

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
                            x: unpack(data, "dt"),
                            y: unpack(data, "pressure"),
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
                            x: unpack(data, "dt"),
                            y: unpack(data, "salinity"),
                            line: {color: "#FF6600"},
                        }],
                        salinity_layout
                    );

                    console.log("hold");
                    icefish_charts =[temperature, salinity, pressure];

                    set_up_events(icefish_charts);

                    INIT = true;
                    console.log("Plotted!");
                },
                error: function(data, status, xhr){
                    console.log("error " + status);
                }
            }
        );
        console.log("Function complete");
    }