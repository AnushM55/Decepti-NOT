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

    function populateTechniques(techniques) {
        const container = document.getElementById('detected-techniques');
        container.innerHTML = '';
        
        techniques.forEach(tech => {
            if( tech !== undefined){
                if(tech.name === undefined){

            const techDiv = document.createElement('div');
            techDiv.className = 'technique-card';
            techDiv.innerHTML = `<h1>${tech}</h1>`
                }else{

            const techDiv = document.createElement('div');
            techDiv.className = 'technique-card';
            techDiv.innerHTML = `
                <h5>${tech.name}</h5>
                <p><strong>Example:</strong> ${tech.example}</p>
                <p>${tech.explanation}</p>
            `;
            container.appendChild(techDiv);
            } 
                }
        });
    }

    function populateMatches(matches) {
        const container = document.getElementById('detailed-matches');
        container.innerHTML = '';
        
        Object.entries(matches).forEach(([type, entries]) => {
            const section = document.createElement('div');
            section.className = 'match-section';
            section.innerHTML = `<h5>${type.replace(/_/g, ' ')}</h5>`;
            
            const list = document.createElement('ul');
            entries.forEach(entry => {
                list.innerHTML += `
                    <li>
                        <p><strong>Match:</strong> ${entry.match}</p>
                        <p><strong>Context:</strong> ...${entry.context}...</p>
                        <p><small>Position: ${entry.position}</small></p>
                    </li>
                `;
            });
            
            section.appendChild(list);
            container.appendChild(section);
        });
    }

    async function analyzeCurrentPage() {
        try {
            showState('loading');

            const [tab] = await chrome.tabs.query({active: true, currentWindow: true});

            const [response] = await chrome.scripting.executeScript({
                target: {tabId: tab.id},
                function: () => {
                    const article = document.querySelector('article') || document.body;
                    return article.innerText;
                }
            });

            const content = response.result;

            const analysisResponse = await fetch('https://newproject-production-4c15.up.railway.app/analyze', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({url: tab.url, content})
            });


            const result = await analysisResponse.json();

            document.getElementById('analysis-result').textContent = result.analysis;
            updateScore(result.propaganda_score);
            
            // Populate corrections
            const resultState = document.getElementById('result-state');
            const correctionSection = document.getElementById('correction-section');
            const correctionList = document.getElementById('correction-list');
            correctionList.innerHTML = '';
            if (result.correction?.length > 0) {
                resultState.classList.remove('d-none');
                result.correction.forEach(item => {
                    console.log(item)
                    const li = document.createElement('li');
                    if (item.suggestion !== undefined && item.example !== undefined){
                    li.innerHTML = `
                    <p>${(item.suggestion!== undefined)?item.suggestion:""}</p>
                    <p>${(item.example !== undefined)?item.example:""}</p>`
                    }else{
                        li.textContent = `${item}`
                    }
                    correctionList.appendChild(li);
                });
                correctionSection.classList.remove('d-none');
            } else {
                correctionSection.classList.add('d-none');
                resultState.classList.add('d-none');
            }

            // Populate techniques
            populateTechniques(result.detected_techniques);
            
            // Populate matches
            populateMatches(result.detailed_matches);

            showState('result');

        } catch (error) {
            document.getElementById('error-message').textContent = 
                'Failed to analyze article. Please check if the backend server is running.';
            console.log(error)
            showState('error');
        }
    }

    // Event Listeners
    document.getElementById('analyze-btn').addEventListener('click', analyzeCurrentPage);
    document.getElementById('analyze-new').addEventListener('click', () => showState('initial'));
    document.getElementById('error-retry').addEventListener('click', analyzeCurrentPage);
});
