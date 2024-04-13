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

function makeTabsWork(textAreaId) {
    var textarea = document.getElementById(textAreaId);

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
}
