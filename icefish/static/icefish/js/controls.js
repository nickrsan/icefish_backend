ICEFISH_WIPER_SECONDS_PER_REVOLUTION = 9;  // measured by Paul and Nick
ICEFISH_WIPER_DEGREES_PER_SECOND = 40;
ICEFISH_WIPER_MS_PER_DEGREE = 25.01088;
ICEFISH_WIPER_BASE_URL = ICEFISH_CONTROL_BASE_URL + ":" + ICEFISH_CONTROL_PORT;
ICEFISH_WIPER_URL_ON = ICEFISH_WIPER_BASE_URL + "/Relays/Turn1On/";
ICEFISH_WIPER_URL_OFF = ICEFISH_WIPER_BASE_URL + "/Relays/Turn1Off/";

function icefish_wiper_toggle(on_off) {
    if (on_off === "on") {
        var url = ICEFISH_WIPER_URL_ON;
    } else {
        var url = ICEFISH_WIPER_URL_OFF;
    }

    $.ajax({
        url: url,
        success: function (data, status, xhr) {
            console.log("Wiper turned " + on_off);
        },
        error: function (data, status, xhr) {
            console.log("Wiper command failed");
        },
    });
}



function icefish_wiper_revolution(num_revolutions){
    icefish_wiper_toggle("on");
    setTimeout(icefish_wiper_toggle, ICEFISH_WIPER_SECONDS_PER_REVOLUTION *1000 * num_revolutions, "off");
}

function icefish_move_wiper(degrees){
    icefish_wiper_toggle("on");
    setTimeout(icefish_wiper_toggle, ICEFISH_WIPER_MS_PER_DEGREE * degrees, "off");
}

function icefish_lights_toggle(on_off){

    var base_url = ICEFISH_CONTROL_BASE_URL + ":" + ICEFISH_CONTROL_PORT + "/Relays/";
    if (on_off === "on") {
        var urls = [base_url + "Turn2On/", base_url + "Turn4On/"]
    } else {
        var urls = [base_url + "Turn2Off/", base_url + "Turn4Off/"]
    }

    urls.forEach(function(url) {

        $.ajax({
            url: url,
            success: function (data, status, xhr) {
                console.log("Wiper turned " + on_off);
            },
            error: function (data, status, xhr) {
                console.log("Wiper command failed");
            },
        })
    });
}