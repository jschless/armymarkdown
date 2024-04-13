function update_progress(status_url, count) {
    // send GET request to status URL
    $.get(status_url, function (data) {
        if (data["state"] == "SUCCESS") {
            $("#status").text("");
	    document.getElementById('progress').style.width = '100%';
	    document.getElementById('progress-bar-container').style.display = 'none';
	    document.getElementById('progress').style.width = '0%';
	    window.open(data["presigned_url"], "_blank"); // support multiple files
            return;
        } else if (data["state"] == "FAILURE") {
            $("#status").text(
		"There was an unknown error with your memo. I know this isn't super helpful, but fix the issue and try again."
            );
        } else {
	    document.getElementById('progress-bar-container').style.display = 'block';

            let rerun_freq = 1000;        
            count += 1;
	    const averageSeconds = 20;
            // rerun in 1 seconds
            if (count < 80) {
		// $("#status").text(
		//     "Waiting for your memo pdf to be generated! Please be patient! It's only been " +
		// 	count * 2 +
		// 	" seconds."
		// );
		let progress = count / averageSeconds * 100;
		document.getElementById('progress').style.width = progress + '%';
        
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
