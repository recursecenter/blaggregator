/*

   This file contains the javascript required to update broken profile images
   of users. The code detects any profile images that are broken, and requests
   the server for new images.  The server inturn requests Hacker School API for
   the update profile image urls and returns them.

*/

function update_avatar_url(img) {
    var author_id = $(img).attr('data-author-id');
    if (author_id) {
        var xhr = $.get('/updated_avatar/' + author_id +'/')
            .done(function(data){
                img.src = data;
            })
    }
}

function update_broken_images(){
    $('img').each(function(index){
        if (this.complete) {
            // check if broken and update
            if (this.naturalWidth === 0) {
                update_avatar_url(this);
            }
        } else {
            // or attach an error handler, to update if broken on load.
            $(this).error(
                function(){
                    // Unbind the error handler, to prevent it from being
                    // called recursively called, if the update image loading
                    // fails too.
                    $(this).unbind('error');
                    update_avatar_url(this);
                }
            );
        }
    });
}

$(document).ready(function(){
    update_broken_images();
});
