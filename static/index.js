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

var textarea = document.getElementById("editor");

textarea.addEventListener("keydown", function(event) {
    if (event.key === "Tab") {
	event.preventDefault();

	var start = this.selectionStart;
	var end = this.selectionEnd;

	// Insert four spaces at the caret position
	this.value = this.value.substring(0, start) + "    " + this.value.substring(end);

	// Move the caret position forward by four spaces
	this.selectionStart = this.selectionEnd = start + 4;
    }
});

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

function generate_memo() {
    button_press("/process", update_progress);
}


function update_progress(status_url, count) {
    // send GET request to status URL
    $.get(status_url, function (data) {
        if (data["state"] == "SUCCESS") {
            $("#status").text("");
	    window.open(data["presigned_url"], "_blank"); // support multiple files
            return;
        } else if (data["state"] == "FAILURE") {
            $("#status").text(
		"There was an unknown error with your memo. I know this isn't super helpful, but fix the issue and try again."
            );
        } else {
            let rerun_freq = 2000;
            count += 1;
            // rerun in 2 seconds
            if (count < 50) {
		$("#status").text(
		    "Waiting for your memo pdf to be generated! Please be patient! It's only been " +
			count * 2 +
			" seconds."
		);
		setTimeout(function () {
		    update_progress(status_url, count);
		}, rerun_freq);
            }
        }
    });
}

$(function () {
    $("#start-bg-job").click(generate_memo);
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


