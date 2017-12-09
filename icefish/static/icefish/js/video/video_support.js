
function recover_video(){
    var video_player = videojs("video_player");
    if (video_player.ended() || video_player.paused()){  // checking this because on some errors it'll play through. Only want to reset the player if it ends
        // Try to recover the stream by starting to play again
        video_player.reset();
        log_error("Player failed - trying to reset it");
    }else{
        log_error("Error passed, but stream not ended - handled");
    }
}
function hide_controls(){
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
    video_player.on("play",  hide_controls);
    video_player.skippy({"maxErrors": 999999, "onLiveError": recover_video});
    video_player.play();
}
