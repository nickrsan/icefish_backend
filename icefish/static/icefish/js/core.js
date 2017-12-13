icefish_open_dialog = null;  // if we open a dialog, store it here so we can close it
main_body_default_class = "pure-u-md-17-24";

panels = {
    "icefish_settings":{
        "container":"icefish_settings",
        "button":"interface_settings_button",
        "open_class":"pure-u-md-1-3",
        "main_class":"pure-u-md-15-24",
        "is_open": false,
    },
    "icefish_video_browser":{
        "container":"icefish_video_browser",
        "button":"video_browse_button",
        "open_class":"pure-u-md-1-2",
        "main_class":"pure-u-md-11-24",
        "is_open": false,
        "on_close": function(){
            videojs("icefish_video_promos_player").pause();
        }
    },
    "icefish_audio_browser":{
        "container":"icefish_audio_browser",
        "button":"audio_browse_button",
        "open_class":"pure-u-md-1-2",
        "main_class":"pure-u-md-11-24",
        "is_open": false,
    },
    "icefish_data_browser":{
        "container":"icefish_data_browser",
        "button":"ctd_data_button",
        "open_class":"pure-u-md-1-2",
        "main_class":"pure-u-md-11-24",
        "is_open": false,
    },
    "icefish_about":{
        "container":"icefish_about",
        "button":"project_about_button",
        "open_class":"pure-u-md-1-2",
        "main_class":"pure-u-md-11-24",
        "is_open": false,
    },
    "icefish_summary_stats":{
        "container":"icefish_summary_stats",
        "button":"project_context_button",
        "open_class":"pure-u-md-1-2",
        "main_class":"pure-u-md-11-24",
        "is_open": false,
    },
    "ptz_controls_button":{
        "container":"icefish_controls",
        "button":"interface_settings_button",
        "open_class":"pure-u-md-1-3",
        "main_class":"pure-u-md-15-24",
        "is_open": false,
    }
};

function swap_panels(new_panel_id){
    /*
        Handles opening and closing panels, when called with no arguments, closes all panels. Panels
        MUST be defined above in the `panels` variable in order to be open or closed, as all the required
        information is defined there.
     */

    var current_panel = null;
    Object.keys(panels).forEach(function(panel_key){
        var panel = panels[panel_key];
        if (panel.is_open){
            $("#"+panel.container).removeClass(panel.open_class).hide("slide");
            $("#"+panel.button).removeClass("active");
            $("#icefish_main").removeClass(panel.main_class).addClass(main_body_default_class);
            panels[panel_key].is_open = false;  // not sure this would work in JS - it's operating on a copy
            if (panel.on_close !== undefined){  // run any callback for closing the panel
                panel.on_close();
            }
            current_panel = panel_key;
        }
    });

    if(new_panel_id !== undefined && current_panel !== new_panel_id){
        var new_panel_settings = panels[new_panel_id];

        $("#"+new_panel_id).addClass(new_panel_settings.open_class).show("slide");
        $("#icefish_main").addClass(new_panel_settings.main_class).removeClass(main_body_default_class);
        $("#"+new_panel_settings.button).addClass("active");
        panels[new_panel_id].is_open = true;
        $("#icefish_charts").hide();
        if($("#icefish_chart_toggle_button").hasClass("fa-caret-right")){
            change_chart_size();
        }
    }else{
        $("#icefish_charts").show();
    }
}

function _log(message, level){
    /*
        A general purpose logger - not looking for anything fancy, but I am looking for something that could handle more
        than just logging to the console - maybe logging some messages to the page at some point
     */
    console.log(level + ": " + message);
}

function log_error(message){
    _log(message, "ERROR");
}

function startup(){
    $( document ).ready(function() {

        get_initial_data({"temperature": "temperature", "pressure": "pressure", "salinity": "salinity"});

        set_up_dialogs();

        videojs.Hls.GOAL_BUFFER_LENGTH = 15;  // on local network, we want to keep this reduced because it keeps pulling too much data and fails otherwise
        videojs.Hls.MAX_GOAL_BUFFER_LENGTH = 30; // same as above - we might want to tweak this to be a local setting when this all goes up online.

        start_video();
        make_video_archive_navigation("video_archive_selector");
    });
}

function set_up_dialogs(){
    /*
        Right now just for making sure that clicks outside of them will cause them to close
     */

    $("#icefish_main").on("click", function(){  // closes open dialogs if we click on the main area
        swap_panels(); // closes all panels when called with no arguments
    });
}