videojs.Hls.GOAL_BUFFER_LENGTH = 10;  // on local network, we want to keep this reduced because it keeps pulling too much data and fails otherwise
videojs.Hls.MAX_GOAL_BUFFER_LENGTH = 20; // same as above - we might want to tweak this to be a local setting when this all goes up online.

function recover_video(){
    /*
        This is an attempt to restart the stream if it fails - documentation on videojs is a little sparse on what these
        functions actually *do*, so this is a guess, and is being tested whenever the stream fails. It's possible that the
        tutorial docs (as opposed to the API docs) in videojs describe more how to handle this
     */
    var video_player = videojs("video_player");
    if (video_player.ended() || video_player.paused()){  // checking this because on some errors it'll play through. Only want to reset the player if it ends
        // Try to recover the stream by starting to play again
        video_player.reset();
        video_player.play();
        log_error("Player failed - trying to reset it");
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
    var video_player = videojs("video_player");
    video_player.on("abort", recover_video);
    video_player.on("ended", function(){
        video_player.controls(true);
        recover_video();
    });
    video_player.on("error", recover_video);
    video_player.on("abort", recover_video);
    //video_player.on("play",  hide_controls);
    //video_player.skippy({"maxErrors": 999999, "onLiveError": recover_video});

    video_player.ready(function(){
        video_player.play();  // only play when ready - this is likely the issue we were having after we swapped from autoplay to this call
    });
}

function create_video(container, src, autoplay, controls){

}