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
