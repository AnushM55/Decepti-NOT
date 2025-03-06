document.addEventListener('DOMContentLoaded', function() {
    const states = {
        initial: document.getElementById('initial-state'),
        loading: document.getElementById('loading-state'),
        result: document.getElementById('result-state'),
        error: document.getElementById('error-state')
    };

    function showState(stateName) {
        Object.entries(states).forEach(([name, element]) => {
            element.classList.toggle('d-none', name !== stateName);
        });
    }

    function updateScore(score) {
        const progressBar = document.getElementById('propaganda-score');
        progressBar.style.width = `${score}%`;
        progressBar.classList.remove('bg-success', 'bg-warning', 'bg-danger');

        if (score < 30) {
            progressBar.classList.add('bg-success');
        } else if (score < 70) {
            progressBar.classList.add('bg-warning');
        } else {
            progressBar.classList.add('bg-danger');
        }

        progressBar.textContent = `${score}%`;
    }

    async function analyzeCurrentPage() {
        try {
            showState('loading');

            // Get current tab
            const [tab] = await chrome.tabs.query({active: true, currentWindow: true});

            // Extract content from the page
            const [response] = await chrome.scripting.executeScript({
                target: {tabId: tab.id},
                function: () => {
                    const article = document.querySelector('article') || document.body;
                    return article.innerText;
                }
            });

            const content = response.result;

            // Send to backend for analysis
            const analysisResponse = await fetch('http://localhost:5000/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    url: tab.url,
                    content: content
                })
            });

            if (!analysisResponse.ok) {
                throw new Error('Analysis failed');
            }

            const result = await analysisResponse.json();

            // Update UI with results
            document.getElementById('analysis-result').textContent = result.analysis;
            updateScore(result.propaganda_score);

            if (result.correction) {
                document.getElementById('correction-section').classList.remove('d-none');
                document.getElementById('correction-text').textContent = result.correction;
            } else {
                document.getElementById('correction-section').classList.add('d-none');
            }

            showState('result');

        } catch (error) {
            document.getElementById('error-message').textContent = 
                'Failed to analyze article. Please check if the backend server is running.';
            showState('error');
        }
    }

    // Event Listeners
    document.getElementById('analyze-btn').addEventListener('click', analyzeCurrentPage);
    document.getElementById('analyze-new').addEventListener('click', () => showState('initial'));
    document.getElementById('error-retry').addEventListener('click', analyzeCurrentPage);
});