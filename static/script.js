document.addEventListener('DOMContentLoaded', function() {
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');
    const downloadBtn = document.getElementById('downloadBtn');
    const keywordsInput = document.getElementById('keywords');
    const locationsInput = document.getElementById('locations');
    const dataCount = document.getElementById('dataCount');
    const statusText = document.getElementById('statusText');
    const dataTable = document.getElementById('dataTable');
    
    let updateInterval;

    // Start scraping
    startBtn.addEventListener('click', async function() {
        const keywords = keywordsInput.value.trim();
        const locations = locationsInput.value.trim();
        
        if (!keywords || !locations) {
            alert('Please enter both keywords and locations');
            return;
        }
        
        // Disable start button, enable others
        startBtn.disabled = true;
        stopBtn.disabled = false;
        // downloadBtn.disabled = false;
        startBtn.classList.add('opacity-50', 'cursor-not-allowed');
        stopBtn.classList.remove('opacity-50', 'cursor-not-allowed');
        
        try {
            const response = await fetch('/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    keywords: keywords,
                    locations: locations
                })
            });
            
            const data = await response.json();
            if (response.ok) {
                statusText.textContent = 'Scraping started...';
                statusText.className = 'text-blue-600 font-bold';
                
                // Start polling for updates
                updateInterval = setInterval(updateStatus, 2000);
            } else {
                throw new Error(data.error || 'Failed to start scraping');
            }
        } catch (error) {
            console.error('Error:', error);
            statusText.textContent = `Error: ${error.message}`;
            statusText.className = 'text-red-600 font-bold';
            resetButtons();
        }
    });
    
    // Stop scraping
    stopBtn.addEventListener('click', async function() {
        try {
            const response = await fetch('/stop', {
                method: 'POST'
            });
            
            const data = await response.json();
            if (response.ok) {
                statusText.textContent = 'Scraping stopped';
                statusText.className = 'text-orange-600 font-bold';
                clearInterval(updateInterval);
                
                // // Enable download button
                // downloadBtn.disabled = false;
                // downloadBtn.classList.remove('opacity-50', 'cursor-not-allowed');
            } else {
                throw new Error(data.error || 'Failed to stop scraping');
            }
        } catch (error) {
            console.error('Error:', error);
            statusText.textContent = `Error: ${error.message}`;
            statusText.className = 'text-red-600 font-bold';
        }
    });
    
    downloadBtn.addEventListener('click', async function() {
        try {
            // First check if we have any data
            const response = await fetch('/get_data');
            const data = await response.json();
            
            if (data.count === 0) {
                alert('No data available to download yet');
                return;
            }
            
            // Proceed with download
            window.location.href = '/download';
        } catch (error) {
            console.error('Error checking data:', error);
            alert('Error checking data availability');
        }
    });
    
    
    // Update status and data display
    async function updateStatus() {
        try {
            const response = await fetch('/status');
            const data = await response.json();
            
            if (response.ok) {
                // Update status
                statusText.textContent = data.status;
                
                // Update count
                dataCount.textContent = data.count;
                
                // Update table with new data
                updateDataTable(data.data);
                
                // If scraping is complete, enable download button
                if (data.status.includes('completed') || data.status.includes('Error')) {
                    clearInterval(updateInterval);
                    // downloadBtn.disabled = false;
                    // downloadBtn.classList.remove('opacity-50', 'cursor-not-allowed');
                    startBtn.disabled = false;
                    startBtn.classList.remove('opacity-50', 'cursor-not-allowed');
                    stopBtn.disabled = true;
                    stopBtn.classList.add('opacity-50', 'cursor-not-allowed');
                }
            }
        } catch (error) {
            console.error('Error fetching status:', error);
        }
    }
    
    // Update the data table
    function updateDataTable(data) {
        // Clear existing rows (except headers)
        dataTable.innerHTML = '';
        
        // Add new rows
        data.forEach(item => {
            const row = document.createElement('tr');
            row.className = 'hover:bg-gray-50';
            
            row.innerHTML = `
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${item.NAME || 'NA'}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${item.ADDRESS || 'NA'}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${item.DEPARTMENT || 'NA'}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${item.PHONE || 'NA'}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-blue-500 hover:text-blue-700">
                    ${item.URL === 'NA' ? 'NA' : `<a href="${item.URL}" target="_blank" class="underline">Visit</a>`}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${item.RATINGS || 'NA'}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${item.TOTAL_REVIEWS || 'NA'}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${item['AVAILABLE_TIMINGS'] || 'NA'}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${item['EMAIL ID'] || 'NA'}</td>
            `;
            
            dataTable.appendChild(row);
        });
    }
    
    // Reset buttons to initial state
    function resetButtons() {
        startBtn.disabled = false;
        stopBtn.disabled = true;
        // downloadBtn.disabled = false;
        startBtn.classList.remove('opacity-50', 'cursor-not-allowed');
        stopBtn.classList.add('opacity-50', 'cursor-not-allowed');
        // downloadBtn.classList.add('opacity-50', 'cursor-not-allowed');
    }
});