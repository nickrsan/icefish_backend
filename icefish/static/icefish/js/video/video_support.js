on_demand_videos = [
    {   path: ICEFISH_VIDEO_SERVER_URL + "/MOO_promos/mp4:moo_video_compilation_1.0.mp4/playlist.m3u8",
        container: "video_archive_container",
        thumbnail: "",
        name: "Observatory Compilation Video",
        type:"application/x-mpegURL",
        id: "icefish_video_moo_compilation"
    },
    {
        path:ICEFISH_VIDEO_SERVER_URL +"/MOO_promos/mp4:short_moo_promo_4.0.mp4/playlist.m3u8",
        container: "video_archive_container",
        name: "Installing the Observatory",
        type:"application/x-mpegURL",
        id: "icefish_video_installing_observatory",
    }
];

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

function switch_video(path, type, container, id){
    var container_element = $("#"+container);
    container_element.empty();  // remove existing video
    _create_video(container, id, path, true, true, true, type);
}

function make_video_archive_navigation(container){
    if(container === null){
        container = $("#video_archive_selector");
    }else{
        container = $("#"+container);
    }

    on_demand_videos.forEach(function(video){
        container.append("<li><a href=\"#\" onclick=\"switch_video('"+video.path+"','"+video.type+"','"+video.container+"','"+video.id+"');\">"+video.name+"</li>");
    });


}

function _create_video(container, video_name, video_path, autoplay, controls, fluid, video_type){
    if (video_name === undefined){
        video_name = "video_player"
    }

    if(video_path === undefined){
        video_path = ICEFISH_VIDEO_SERVER_URL +"/MOO/smil:AdaptaMooHigh.smil/playlist.m3u8";
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

    if (video_type === undefined){
        video_type = "application/x-mpegURL"
    }

    $("#"+container).append("             <video id=\""+video_name+"\" class=\"vjs-default-skin pure-u-md-1-1 icefish_fluid\">\n" +
        "                    <source src=\"" + video_path +"\" type=\"application/x-mpegURL\">\n" +
        "                </video>");

    return videojs(video_name, {"autoplay": autoplay,
                                            "controls": controls
    });
}