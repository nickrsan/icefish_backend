icefish_open_dialog = null;  // if we open a dialog, store it here so we can close it

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


function toggle_dialog(id, icon_id, main_body_new_class){
    var transition = null;
    var toggle_main = null;
    if (icefish_open_dialog === null){  // there's nothing open already
        transition = "slide";
        icefish_open_dialog = {"id": id, "icon_id": icon_id};
        toggle_main = true;
    }else if (icefish_open_dialog.id === id || (id === false && icefish_open_dialog !== null)){  // close *any* open dialogs if we pass in false and something is open
        transition = "slide";
        if (id === false){
            id = icefish_open_dialog.id;  // save it because we'll use it to close it
            $("#"+icefish_open_dialog.icon_id).toggleClass("active");
        }
        icefish_open_dialog = null;
        toggle_main = true;
    }else{  // something is open already, swap it
        $("#"+icefish_open_dialog.id).toggle();
        $("#"+icefish_open_dialog.icon_id).toggleClass("active");
        icefish_open_dialog = {"id": id, "icon_id": icon_id};
        toggle_main = false; // don't do anything to the main divs if we're just swapping open panels
    }

    if (main_body_new_class === undefined){ // if it wasn't passed in, here's the default
        main_body_new_class = "pure-u-md-7-24"  // we pass it in for smaller panels
    }

    $("#"+id).toggle(transition);

    $("#"+icon_id).toggleClass("active");

    if (toggle_main === true){
        $("#icefish_main").toggleClass("pure-u-md-17-24 " + main_body_new_class);  // first is original, second is updated
        $("#icefish_charts").toggle();  // first is original, second is updated
    }
}