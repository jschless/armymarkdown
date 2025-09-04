function findHighest(prefix) {
    let highestNumber = 0;

    document.querySelectorAll("[id^='" + prefix + "']").forEach(function(element) {
	const idNumber = parseInt(element.id.replace(prefix, ""));
	if (idNumber > highestNumber) {
            highestNumber = idNumber;
	}
    });

    return highestNumber;
}

let forCount = findHighest("for");
let thruCount = findHighest("thru");
let encCount = findHighest("enc");
let distroCount = findHighest("distro");
let cfCount = findHighest("cf");

const suffixToVarMap = {
    "for": forCount,
    "thru": thruCount,
    "enc": encCount,
    "distro": distroCount,
    "cf": cfCount   
};

function addAddress(fields, is_for) {
    // reuse this for thru and for address buttons
    let newRow = document.createElement('div');
    newRow.classList.add("row")
    let newDiv = document.createElement('div');
    newDiv.classList.add("six");
    newDiv.classList.add("columns");
    console.log(forCount, thruCount);
    is_for ? forCount++ : thruCount++; 

    const suffix = is_for ? forCount : thruCount;
    
    fields.forEach(function(field) {
	let label = document.createElement('label');
	label.textContent = field.label;
	label.classList.add("u-full-width");
	label.classList.add("center");
	label.setAttribute('for', field.id + suffix);

	
	let input = document.createElement('input');
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

    let deleteButton = document.createElement('button');
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
    let div = document.createElement('div');
    div.id = divId;
    let label = document.createElement('label');
    label.textContent = name;
    label.classList.add("u-full-width");
    label.classList.add("center");
    label.setAttribute('for', "TITLE");
    
    let input = document.createElement('input');
    input.type = 'text';
    input.id = id;
    input.name = id;
    input.value = value;
    input.classList.add("u-full-width");
    input.classList.add("center");
    
    div.append(label);
    div.append(input);
    
    let deleteButton = document.createElement('button');
    let addButton = document.getElementById(addId);

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
    let targetDiv = document.getElementById(targetLocationId);
    let inputElement = document.createElement('input');
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
    let div = document.createElement('div');
    let label = document.createElement('label');
    suffixToVarMap[suffix]++;
    let count = suffixToVarMap[suffix];
    
    label.textContent = labelText;
    label.classList.add("u-full-width");
    label.classList.add("center");

    let input = document.createElement('input');
    input.type = 'text';
    if (suffix == "enc") {
	input.id = "ENCLOSURE" + count;
	input.name = "ENCLOSURE" + count;
    } else {
	input.id = suffix.toUpperCase() + count;
	input.name = suffix.toUpperCase() + count;
    }
    input.value = inputValue;
    input.classList.add("u-full-width");
    input.classList.add("center");

    div.append(label);
    div.append(input);

    let deleteButton = document.createElement('button');
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
    const fields = [
	{ id: "FOR_ORGANIZATION_NAME", placeholder: "U.S. Army Command and General Staff College (ATZL)", label: "FOR Organization Name"},
	{ id: "FOR_ORGANIZATION_STREET_ADDRESS", placeholder: "100 Stimson Avenue", label: "FOR Street Address"},
	{ id: "FOR_ORGANIZATION_CITY_STATE_ZIP", placeholder: "Ft Leavenworth, KS 66027-1352", label: "FOR City, State Zip"}
    ];

    addAddress(fields, true);
}

function addThruAddress() {
    const fields = [
	{ id: "THRU_ORGANIZATION_NAME", placeholder: "U.S. Army Command and General Staff College (ATZL)", label: "THRU Organization Name"},
	{ id: "THRU_ORGANIZATION_STREET_ADDRESS", placeholder: "100 Stimson Avenue", label: "THRU Street Address"},
	{ id: "THRU_ORGANIZATION_CITY_STATE_ZIP", placeholder: "Ft Leavenworth, KS 66027-1352", label: "THRU City, State Zip"}
    ];

    addAddress(fields, false);
}


function deleteElement(elementId) {
    let element = document.getElementById(elementId);
    if (element) {
	element.remove();
    } else {
	console.log("Element with ID " + elementId + " not found.");
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const currentDate = new Date();    
    const options = { day: 'numeric', month: 'long', year: 'numeric' };    
    const formattedDate = currentDate.toLocaleDateString('en-GB', options);
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
});

makeTabsWork("MEMO_TEXT");

document.addEventListener('DOMContentLoaded', function() {
    const saveProgressButton = document.getElementById("save-progress");
    
    if (saveProgressButton) {
        saveProgressButton.addEventListener("click", function(e) {
            e.preventDefault(); 
            saveData();
        });
    }

    const memoForm = document.getElementById('memo');

    if (memoForm) {
        memoForm.addEventListener("submit", function(e) {
            e.preventDefault(); 
            buttonPress("/process", updateProgress); 
        });
    }
});
