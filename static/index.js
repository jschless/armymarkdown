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
    const reviewMemoButton = document.getElementById('review-memo');

    if (startBgJobButton) {
        startBgJobButton.addEventListener('click', function(event) {
            event.preventDefault();
            buttonPress('/process', updateProgress);
        });
    }

    if (reviewMemoButton) {
        reviewMemoButton.addEventListener('click', function(event) {
            event.preventDefault();
            window.reviewMemo('/review/memo');
        });
    }
});
