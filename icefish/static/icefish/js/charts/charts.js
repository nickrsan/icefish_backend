function unpack(rows, key) {
        return rows.map(function(row) { return row[key]; });
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
                    Plotly.plot(temperature, [{
                            x: unpack(data, "dt"),
                            y: unpack(data, "temp"),
                            name: "Temperature (C)"
                        }, {x: unpack(data, "dt"),
                            y: unpack(data, "freezing_point"),
                            name: "Freezing Point"}

                        ], {
                            xaxis: {title: 'Time'},
                            yaxis: {title: 'Temperature', range:[-1.92, -1.905]},
                            margin: {t: 20},
                            hovermode: 'closest'
                        }
                    );
                    Plotly.plot(pressure, [{
                            x: unpack(data, "dt"),
                            y: unpack(data, "pressure"),
                        }], {
                            xaxis: {title: 'Time'},
                            yaxis: {title: 'Pressure', range:[18.7,19]},
                            margin: {t: 20},
                            hovermode: 'closest'
                        }
                    );
                    Plotly.plot(salinity, [{
                            x: unpack(data, "dt"),
                            y: unpack(data, "salinity"),
                            line: {color: "#FF6600"},
                        }], {
                            xaxis: {title: 'Time'},
                            yaxis: {title: 'Salinity', range:[34.62,34.66]},
                            margin: {t: 20},
                            hovermode: 'closest'
                        }
                    );


                    console.log("Plotted!");
                },
                error: function(data, status, xhr){
                    console.log("error " + status);
                }
            }
        );
        console.log("Function complete");
    }