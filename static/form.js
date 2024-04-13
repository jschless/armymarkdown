function findHighest(prefix) {
    var highestNumber = 0;

    document.querySelectorAll("[id^='" + prefix + "']").forEach(function(element) {
	var idNumber = parseInt(element.id.replace(prefix, ""));
	if (idNumber > highestNumber) {
            highestNumber = idNumber;
	}
    });

    return highestNumber;
}

var forCount = findHighest("for");
var thruCount = findHighest("thru");
var encCount = findHighest("enc");
var distroCount = findHighest("distro");
var cfCount = findHighest("cf");

var suffixToVarMap = {
    "for": forCount,
    "thru": thruCount,
    "enc": encCount,
    "distro": distroCount,
    "cf": cfCount   
};

function addAddress(fields, is_for) {
    // reuse this for thru and for address buttons
    var newRow = document.createElement('div');
    newRow.classList.add("row")
    var newDiv = document.createElement('div');
    newDiv.classList.add("six");
    newDiv.classList.add("columns");
    console.log(forCount, thruCount);
    is_for ? forCount++ : thruCount++; 

    var suffix = is_for ? forCount : thruCount;
    
    fields.forEach(function(field) {
	var label = document.createElement('label');
	label.textContent = field.label;
	label.classList.add("u-full-width");
	label.classList.add("center");
	label.setAttribute('for', field.id + suffix);

	
	var input = document.createElement('input');
	input.type = 'text';
	input.id = field.id + suffix;
	input.name = field.id + suffix;
	input.placeholder = field.placeholder;
	input.value = field.placeholder;
	input.classList.add("u-full-width");
	input.classList.add("center");

	
	newDiv.append(label);
	newDiv.append(input);
	newDiv.append(document.createElement('br')); // Add line break

    });

    var deleteButton = document.createElement('button');
    deleteButton.textContent = is_for ? 'Delete FOR address' : 'Delete THRU address';
    deleteButton.classList.add("u-full-width");
    deleteButton.classList.add("center");

    deleteButton.addEventListener('click', function() {
	newRow.remove();
    });
    newDiv.append(deleteButton);

    newDiv.append(document.createElement('hr'));
    newRow.append(newDiv);
    console.log("trying to add", newDiv);
    whereToAdd = is_for ? "forFieldContainer" : "thruFieldContainer";
    document.getElementById(whereToAdd).prepend(newRow);

}

function addDocumentMark(){
    addSingleField("Document Mark", "DOCUMENT_MARK", "CUI", "document_mark", "removeDocumentMark", removeDocumentMark, "documentMarkDiv", "addDocumentMark");   
}

function removeDocumentMark(){
    removeSingleField("documentMarkDiv", "document_mark", "addDocumentMark", "Add Document Mark", addDocumentMark);
}


function addAuthority(){
    addSingleField("Authority", "AUTHORITY", "GEN Milley", "authority", "removeAuthority", removeAuthority, "authorityDiv", "addAuthority");   
}

function removeAuthority(){
    removeSingleField("authorityDiv", "authority", "addAuthority", "Add Authority", addAuthority);
}


function addSuspense(){
    addSingleField("Suspense Date", "SUSPENSE", "08 May 2026", "suspense", "removeSuspense", removeSuspense, "suspenseDiv", "addSuspense");   
}

function removeSuspense(){
    removeSingleField("suspenseDiv", "suspense", "addSuspense", "Add Suspense", addSuspense);
}


function addTitle(){
    addSingleField("Title", "TITLE", "Lost Private", "signature", "removeTitle", removeTitle, "titleDiv", "addTitle");   
}

function removeTitle(){
    removeSingleField("titleDiv", "signature", "addTitle", "Add Title", addTitle);
}

function addSingleField(name, id, value, targetDivId, deleteId, removeFunc, divId, addId) {
    var div = document.createElement('div');
    div.id = divId;
    var label = document.createElement('label');
    label.textContent = name;
    label.classList.add("u-full-width");
    label.classList.add("center");
    label.setAttribute('for', "TITLE");
    
    
    var input = document.createElement('input');
    input.type = 'text';
    input.id = id;
    input.name = id;
    input.value = value;
    input.classList.add("u-full-width");
    input.classList.add("center");

    
    div.append(label);
    div.append(input);

    
    var deleteButton = document.createElement('button');
    var addButton = document.getElementById(addId);

    addButton.remove();

    deleteButton.textContent = 'Remove ' + name;
    deleteButton.classList.add("u-full-width");
    deleteButton.classList.add("center");
    deleteButton.id = deleteId;
    deleteButton.addEventListener('click', removeFunc);
    
    div.append(deleteButton);
    document.getElementById(targetDivId).append(div);
}

function removeSingleField(targetDivId, targetLocationId, buttonId, buttonText, buttonFunc) {
    document.getElementById(targetDivId).remove();
    var targetDiv = document.getElementById(targetLocationId);
    var inputElement = document.createElement('input');
    inputElement.setAttribute('type', 'button');
    inputElement.setAttribute('id', buttonId);
    inputElement.setAttribute('value', buttonText);
    inputElement.classList.add('u-full-width');
    inputElement.classList.add('center');
    inputElement.addEventListener('click', buttonFunc);
    targetDiv.append(inputElement);
}


function addEnclosure() {
    addField("enc", "Enclosure", "Enclosure Name", "enclosures");
}

function addDistro() {
    addField("distro", "Distribution", "Distribution Name", "distributions");
}

function addCF() {
    addField("cf", "Copies Furnished", "Copies Furnished Name", "cfs");
}

function addField(suffix, labelText, inputValue, divId) {
    var div = document.createElement('div');
    var label = document.createElement('label');
    suffixToVarMap[suffix]++;
    var count = suffixToVarMap[suffix];
    
    label.textContent = labelText;
    label.classList.add("u-full-width");
    label.classList.add("center");

    var input = document.createElement('input');
    input.type = 'text';
    input.id = suffix + count;
    input.name = suffix + count;
    input.value = inputValue;
    input.classList.add("u-full-width");
    input.classList.add("center");

    div.append(label);
    div.append(input);

    var deleteButton = document.createElement('button');
    deleteButton.classList.add("u-full-width");
    deleteButton.classList.add("center");
    deleteButton.type = 'text';
    deleteButton.textContent = 'Remove ' + labelText;
    deleteButton.addEventListener('click', function() {
	div.remove();
    });
    div.append(deleteButton);
    div.append(document.createElement('hr'));
    document.getElementById(divId).prepend(div);      
}

function addForAddress() {
    var fields = [
	{ id: "FOR_ORGANIZATION_NAME", placeholder: "U.S. Army Command and General Staff College (ATZL)", label: "FOR Organization Name"},
	{ id: "FOR_ORGANIZATION_STREET_ADDRESS", placeholder: "100 Stimson Avenue", label: "FOR Street Address"},
	{ id: "FOR_ORGANIZATION_CITY_STATE_ZIP", placeholder: "Ft Leavenworth, KS 66027-1352", label: "FOR City, State Zip"}
    ];

    addAddress(fields, true);
}

function addThruAddress() {
    var fields = [
	{ id: "THRU_ORGANIZATION_NAME", placeholder: "U.S. Army Command and General Staff College (ATZL)", label: "THRU Organization Name"},
	{ id: "THRU_ORGANIZATION_STREET_ADDRESS", placeholder: "100 Stimson Avenue", label: "THRU Street Address"},
	{ id: "THRU_ORGANIZATION_CITY_STATE_ZIP", placeholder: "Ft Leavenworth, KS 66027-1352", label: "THRU City, State Zip"}
    ];

    addAddress(fields, false);
}

document.addEventListener('DOMContentLoaded', function() {
    var urlParams = new URLSearchParams(window.location.search);
    var exampleFile = urlParams.get('example_file');
    // Loop through the options and find the one that matches the current URL
    var linkSelector = document.getElementById('linkSelector');
    for (var i = 0; i < linkSelector.options.length; i++) {       
	var option = linkSelector.options[i];
	if (option.id === exampleFile) {
	    option.selected = true;
	    break;
	}
    }

    var currentDate = new Date();    
    var options = { day: 'numeric', month: 'long', year: 'numeric' };    
    var formattedDate = currentDate.toLocaleDateString('en-GB', options);
    document.getElementById('DATE').value = formattedDate;

    document.getElementById('addFOR').addEventListener('click', addForAddress);
    document.getElementById('addTHRU').addEventListener('click', addThruAddress);
    document.getElementById('addEnclosure').addEventListener('click', addEnclosure);
    document.getElementById('addDistro').addEventListener('click', addDistro);
    document.getElementById('addCF').addEventListener('click', addCF);
    if (document.getElementById('removeTitle')) {
	document.getElementById('removeTitle').addEventListener('click', removeTitle);
    }
    if (document.getElementById('addTitle')) {
	document.getElementById('addTitle').addEventListener('click', addTitle);     
    }
    if (document.getElementById('removeSuspense')) {
	document.getElementById('removeSuspense').addEventListener('click', removeSuspense);
    }
    if (document.getElementById('addSuspense')) {
	document.getElementById('addSuspense').addEventListener('click', addSuspense);     
    }
    if (document.getElementById('removeAuthority')) {
	document.getElementById('removeAuthority').addEventListener('click', removeAuthority);
    }
    if (document.getElementById('addAuthority')) {
	document.getElementById('addAuthority').addEventListener('click', addAuthority);     
    }
    if (document.getElementById('removeDocumentMark')) {
	document.getElementById('removeDocumentMark').addEventListener('click', removeDocumentMark);
    }
    if (document.getElementById('addDocumentMark')) {
	document.getElementById('addDocumentMark').addEventListener('click', addDocumentMark);     
    }

});

// allows tab in the text area to indent
var textarea = document.getElementById("MEMO_TEXT");

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
    var formData = new FormData(document.getElementById('memo')); 
    $.ajax({
	type: "POST",
	url: endpoint,
	data: formData,
	processData: false, // Prevent jQuery from processing the data
	contentType: false, // Prevent jQuery from setting the Content-Type header
	success: function (data, status, request) {
	    status_url = request.getResponseHeader("Location");
	    polling_function(status_url, 0);
	},
	error: function (XMLHttpRequest, text, e) {
	    alert("ERROR WHEN PARSING INPUT\n\n" + XMLHttpRequest.responseText);
	},
    });
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

function deleteElement(elementId) {
    var element = document.getElementById(elementId);
    if (element) {
	element.remove();
    } else {
	console.log("Element with ID " + elementId + " not found.");
    }
}

$('#memo').submit(function(e){
    e.preventDefault();
    button_press("/form", update_progress);
});

function changeHref() {
    var selectElement = document.getElementById("linkSelector");
    var selectedValue = selectElement.options[selectElement.selectedIndex].value;     
    window.location.href = selectedValue;
}
