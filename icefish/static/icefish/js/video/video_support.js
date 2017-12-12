function recover_video(player, force){
    /*
        This is an attempt to restart the stream if it fails - documentation on videojs is a little sparse on what these
        functions actually *do*, so this is a guess, and is being tested whenever the stream fails. It's possible that the
        tutorial docs (as opposed to the API docs) in videojs describe more how to handle this
     */
    if (player === undefined){
        player = "video_player" // our default player
    }

    var video_player = videojs(player);
    if (video_player.ended() || video_player.paused() || force === true){  // checking this because on some errors it'll play through. Only want to reset the player if it ends
        // Try to recover the stream by starting to play again
        log_error("Player failed - trying to reset it");
        video_player.dispose();  // destroy and recreate it
        start_video();  // destroy and recreate it
    }else{
        log_error("Error passed, but stream not ended - skipping handling");
    }
}
function hide_controls(){
    /*
        This needs more testing before it can be used again - we wanted to show controls on failure, then hide them upon
        stream starting - we were getting an error, though maybe that was because of a resolved race condition
     */
    if (video_player.userActive !== true){  // only hide the controls if nobody is there right now
        video_player.controls(false);
    }else {
        video_player.on("userinactive", function () {
            video_player.controls(false);
        })
    }
}
function start_video(){
    var video_player = _create_video("icefish_video_player_container", "video_player", true, false, true);
    video_player.on("ready", function() {
        video_player.on("abort", recover_video);
        video_player.on("ended", function () {
            video_player.controls(true);
            recover_video();
        });
        video_player.on("error", recover_video);

        video_player.play();
    });
}

function _create_video(container, video_name, autoplay, controls, fluid){
    if (video_name === undefined){
        video_name = "video_player"
    }

    if (controls === undefined){
        controls = true;
    }

    if (fluid === undefined || fluid === true){
        $("#"+container).addClass("icefish_fluid");  // when initializing this way, vjs-fluid just adds some weird padding - not sure if I'm doing something wrong with the container, but tried a lot - setting our own class instead works
    }

    if (autoplay === undefined){
        autoplay = false;
    }

    $("#"+container).append("             <video id=\"video_player\" class=\"vjs-default-skin pure-u-md-1-1 icefish_fluid\">\n" +
        "                    <source src=\"" +ICEFISH_VIDEO_SERVER_URL +"/MOO/smil:AdaptaMooHigh.smil/playlist.m3u8\" type=\"application/x-mpegURL\">\n" +
        "                </video>");

    return videojs(video_name, {"autoplay": autoplay,
                                            "controls": controls
    });
}