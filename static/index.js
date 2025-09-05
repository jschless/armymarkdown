makeTabsWork('editor');

document.addEventListener('DOMContentLoaded', function() {
    const saveProgressButton = document.getElementById('save-progress');
    
    if (saveProgressButton) {
        saveProgressButton.addEventListener('click', function(e) {
            e.preventDefault();
            saveData();
        });
    }
    const startBgJobButton = document.getElementById('start-bg-job');

    if (startBgJobButton) {
        startBgJobButton.addEventListener('click', function(event) {
            event.preventDefault(); 
            buttonPress('/process', updateProgress); 
        });
    }
});
