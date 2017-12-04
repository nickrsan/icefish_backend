ICEFISH_WIPER_SECONDS_PER_REVOLUTION = 9;  // measured by Paul and Nick
ICEFISH_WIPER_DEGREES_PER_SECOND = 40;
ICEFISH_WIPER_MS_PER_DEGREE = 25.01088;
ICEFISH_WIPER_BASE_URL = ICEFISH_CONTROL_BASE_URL + ":" + ICEFISH_CONTROL_PORT;
ICEFISH_WIPER_URL_ON = ICEFISH_WIPER_BASE_URL + "/Relays/Turn1On/";
ICEFISH_WIPER_URL_OFF = ICEFISH_WIPER_BASE_URL + "/Relays/Turn1Off/";

function icefish_wiper_on_off(on_off) {
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
    })
}



function icefish_wiper_revolution(num_revolutions){
    icefish_wiper_on_off("on");
    setTimeout(icefish_wiper_on_off, ICEFISH_WIPER_SECONDS_PER_REVOLUTION *1000 * num_revolutions, "off");
}

function move_wiper(degrees){
    icefish_wiper_on_off("on");
    setTimeout(icefish_wiper_on_off, ICEFISH_WIPER_MS_PER_DEGREE * degrees, "off");
}