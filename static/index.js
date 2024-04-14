function changeHref() {
    var selectElement = document.getElementById("linkSelector");
    var selectedValue = selectElement.options[selectElement.selectedIndex].value;     
    window.location.href = selectedValue;
}

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

function button_press(endpoint, polling_function) {
    $.ajax({
        type: "POST",
        url: endpoint,
        data: { memo_text: $("#editor").val() },
        success: function (data, status, request) {
            status_url = request.getResponseHeader("Location");
            polling_function(status_url, 0);
        },
        error: function (XMLHttpRequest, text, e) {
            alert("ERROR WHEN PARSING INPUT\n\n" + XMLHttpRequest.responseText);
        },
    });
}



$(function () {
    $("#start-bg-job").click(function() {
	button_press("/process", update_progress);
    });
});

function saveData() {
    var inputData = document.getElementById('editor').value;
    fetch('/save_progress', {
	method: 'POST',
	headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
	},
	body: 'input_data=' + encodeURIComponent(inputData)
    })
	.then(response => {
            console.log('Data saved successfully');
	    location.reload();	   
            $("#editor").val(inputData);
	    
	})
	.catch(error => {
            console.error('Error saving data:', error);
	});
}

$(function () {
    $("#save-progress").click(saveData);
});
