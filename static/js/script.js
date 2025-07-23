// static/js/script.js

// Load team summary
function loadTeamSummary() {
    fetch('/api/team-summary')
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById('team-summary');
            if (data.error) {
                container.innerHTML = `<div class="error">Error: ${data.error}</div>`;
            } else {
                const winRate = data.total_matches > 0 ? ((data.wins / data.total_matches) * 100).toFixed(1) : '0.0';
                const goalDiff = (data.goals_for || 0) - (data.goals_against || 0);
                
                container.innerHTML = `
                    <div class="stat-item">
                        <div class="stat-number">${data.total_matches || 0}</div>
                        <div class="stat-label">Matches</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">${data.wins || 0}-${data.draws || 0}-${data.losses || 0}</div>
                        <div class="stat-label">W-D-L</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">${winRate}%</div>
                        <div class="stat-label">Win Rate</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">${goalDiff >= 0 ? '+' : ''}${goalDiff}</div>
                        <div class="stat-label">Goal Diff</div>
                    </div>
                `;
            }
        })
        .catch(error => {
            document.getElementById('team-summary').innerHTML = `<div class="error">Failed to load team stats</div>`;
        });
}

// Load recent matches
function loadRecentMatches() {
    fetch('/api/recent-matches')
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById('recent-matches');
            if (data.length === 0) {
                container.innerHTML = '<div class="no-data">No recent matches found</div>';
            } else {
                let tableHTML = `
                    <div class="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th>Date</th>
                                    <th>Opponent</th>
                                    <th>Result</th>
                                    <th>Score</th>
                                </tr>
                            </thead>
                            <tbody>
                `;
                
                data.slice(0, 5).forEach(match => {
                    const resultClass = match.Result === 'W' ? 'win' : match.Result === 'L' ? 'loss' : 'draw';
                    tableHTML += `
                        <tr>
                            <td>${match.Date || 'TBD'}</td>
                            <td>${match.Opponent || 'TBD'}</td>
                            <td><span class="${resultClass}">${match.Result || '-'}</span></td>
                            <td>${match.goals_for || 0} - ${match.goals_against || 0}</td>
                        </tr>
                    `;
                });
                
                tableHTML += '</tbody></table></div>';
                container.innerHTML = tableHTML;
            }
        })
        .catch(error => {
            document.getElementById('recent-matches').innerHTML = '<div class="error">Failed to load matches</div>';
        });
}

// Load player stats
function loadPlayerStats() {
    fetch('/api/player-stats')
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById('player-stats');
            if (data.error) {
                container.innerHTML = `<div class="error">Error: ${data.error}</div>`;
            } else if (data.data && data.data.length > 0) {
                let tableHTML = '<div class="table-container"><table><thead><tr>';
                
                const firstRow = data.data[0];
                const columns = Object.keys(firstRow).slice(0, 6);
                columns.forEach(col => {
                    tableHTML += `<th>${col.replace(/Unnamed_\d+_level_0_/, '').replace(/_/g, ' ')}</th>`;
                });
                tableHTML += '</tr></thead><tbody>';
                
                data.data.forEach(player => {
                    tableHTML += '<tr>';
                    columns.forEach(col => {
                        tableHTML += `<td>${player[col] || '-'}</td>`;
                    });
                    tableHTML += '</tr>';
                });
                
                tableHTML += '</tbody></table></div>';
                container.innerHTML = tableHTML;
            } else {
                container.innerHTML = '<div class="no-data">No player data available</div>';
            }
        })
        .catch(error => {
            document.getElementById('player-stats').innerHTML = '<div class="error">Failed to load player stats</div>';
        });
}

// Load database info
function loadDatabaseInfo() {
    fetch('/api/database-info')
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById('database-info');
            if (data.error) {
                container.innerHTML = `<div class="error">Error: ${data.error}</div>`;
            } else {
                let infoHTML = '<div class="table-list">';
                data.forEach(table => {
                    infoHTML += `
                        <div class="table-item">
                            <strong>${table.name.replace(/_/g, ' ')}</strong><br>
                            ${table.rows} rows
                        </div>
                    `;
                });
                infoHTML += '</div>';
                container.innerHTML = infoHTML;
            }
        })
        .catch(error => {
            document.getElementById('database-info').innerHTML = '<div class="error">Failed to load database info</div>';
        });
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    loadTeamSummary();
    loadRecentMatches();
    loadPlayerStats();
    loadDatabaseInfo();
});