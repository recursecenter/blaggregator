/*

   This file currently has only the javascript required to show a confirmation
   button when a user is deleting their blog.  Rename or move stuff around,
   when more javascript gets added.

*/

function show_confirmation(evt){
    $('#delete-button').toggle();
    $('#confirm-button').toggle();
}

$(document).ready(function(){
    $('#delete-button').click(show_confirmation);
});
