document.addEventListener('DOMContentLoaded', function() {
    var currentUrl = window.location.pathname;
    // Loop through the options and find the one that matches the current URL
    var linkSelector = document.getElementById('linkSelector');
    for (var i = 0; i < linkSelector.options.length; i++) {       
	var option = linkSelector.options[i];
	if (option.value === currentUrl) {
            // Set the text of the option to the current URL
            option.selected = true;
            break;
	}
    }
});

makeTabsWork("editor");

$(function () {
    $("#save-progress").click(function(e){
	e.preventDefault();
	saveData();
    });
});

$('#memo').submit(function(e){
    e.preventDefault();
    buttonPress("/process", updateProgress);
});
