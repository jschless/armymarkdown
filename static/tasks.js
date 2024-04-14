function update_progress(status_url, count) {
    // send GET request to status URL
    $.get(status_url, function (data) {
        if (data["state"] == "SUCCESS") {

	    $("#status").text("");
	    windowOpened = window.open(data["presigned_url"], "_blank");
	    if (windowOpened == null ) {
		// Create a button to retrieve memo on user click
		var button = document.createElement('button');
		button.textContent = 'Click to open memo';
		button.addEventListener('click', function() {
		    window.open(data["presigned_url"], "_blank"); // support multiple files
		    document.getElementById('progress-bar').style.width = '100%';
		    document.getElementById('progress-bar-container').style.display = 'none';
		    document.getElementById('progress-bar-container').style.opacity = '.5';
		    document.getElementById('progress').style.width = '0%';
		    document.getElementById("temp_button").remove();
		});
		// button.classList.add("u-full-width");
		button.style.margin = '20px';
		button.classList.add("center");
		button.setAttribute('id', "temp_button");

		var container = document.getElementById('progress-bar-container');		
		container.style.opacity ='1';
		container.append(document.createElement('br'));
		container.appendChild(button);	    	
	    } else {
		document.getElementById('progress-bar-container').style.display = 'none';
		document.getElementById('progress-bar').style.width = '100%';
		document.getElementById('progress').style.width = '0%';
		
	    }	    
            return;
        } else if (data["state"] == "FAILURE") {
            $("#status").text(
		"There was an unknown error with your memo. I know this isn't super helpful, but fix the issue and try again."
            );
        } else {
	    document.getElementById('progress-bar-container').style.display = 'block';

            let rerun_freq = 1000;        
            count += 1;
	    const averageSeconds = 10;
            // rerun in 1 seconds
            if (count < 80) {
		// newWindow.document.write(
		//      "Waiting for your memo pdf to be generated! Please be patient! It's only been " +
		//  	count +	" seconds."
		// );
		let progress = Math.min(count / averageSeconds * 100, 100);
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
