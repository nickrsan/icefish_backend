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