// flight-display.js





class FlightDisplay {
    constructor(flightCategory, fileMap) {
        console.log("16. FlightDisplay Constructor called");
        this.flightCategory = flightCategory;
        this.fileMap = fileMap;
        this.uniqueIdToFileMap = this.createUniqueIdToFileMap();
        console.log("17. FlightDisplay Constructor - flightCategory:", flightCategory);
        console.log("18. FlightDisplay Constructor - fileMap:", fileMap);
    }
    createUniqueIdToFileMap() {
        const map = new Map();
        this.fileMap.forEach((file, key) => {
            const originalFileName = file.name.toUpperCase();
            this.flightCategory['unique identifiers in flight'].forEach(uniqueId => {
                if (uniqueId.toUpperCase().endsWith(originalFileName)) {
                    map.set(uniqueId, file);
                }
            });
        });
        return map;
    }
    getClassName() {
        console.log("19. Getting class name");
        return 'flight-item';
    }

    createDOMElement() {
        console.log("20. Creating DOM element for flight");
        try {
            const flightItem = document.createElement('div');
            flightItem.className = this.getClassName();
            
            console.log("21. Creating photo placeholder");
            flightItem.appendChild(this.createPhotoPlaceholder());
            
            console.log("22. DOM element created");
            return flightItem;
        } catch (error) {
            console.error("Error in createDOMElement:", error);
            throw error;
        }
    }

    createPhotoPlaceholder() {
        console.log("Creating photo placeholder");
        const photoPlaceholder = document.createElement('div');
        photoPlaceholder.className = 'flight-photo-placeholder';

        console.log("Full flightCategory object:", this.flightCategory);
        console.log("Photo Count:", this.flightCategory.photo_count);
        console.log("Unique Identifiers:", this.flightCategory['unique identifiers in flight']);
        console.log("Unique ID to File Map:", this.uniqueIdToFileMap);

        if (this.flightCategory.photo_count > 0 && 
            Array.isArray(this.flightCategory['unique identifiers in flight']) && 
            this.flightCategory['unique identifiers in flight'].length > 0
        ) {
            console.log("Photos available, attempting to display");
            const firstPhotoId = this.flightCategory['unique identifiers in flight'][0];
            console.log("First Photo ID:", firstPhotoId);

            const file = this.uniqueIdToFileMap.get(firstPhotoId);
            console.log("Retrieved File:", file);

            if (file) {
                console.log("File found, creating image element");
                const img = document.createElement('img');
                this.loadAndResizeImage(file, img);
                photoPlaceholder.appendChild(img);
            } else {
                console.warn("File not found in uniqueIdToFileMap.");
                photoPlaceholder.textContent = 'Photo Not Found';
            }
        } else {
            console.log("No photos available or unique identifiers missing");
            if (this.flightCategory.photo_count > 0) {
                photoPlaceholder.textContent = 'Photos exist but identifiers are missing';
            } else {
                photoPlaceholder.textContent = 'Missing photos or wrong gimbal angle';
            }
        }
        
        console.log("Photo placeholder created");
        return photoPlaceholder;
    }

    loadAndResizeImage(file, imgElement) {
        const reader = new FileReader();

        reader.onload = (event) => {
            

            const img = new Image();
            img.onload = () => {
                console.log("Original Image Dimensions:", img.width, img.height);

                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');
                const maxSize = 300; 
                let width = img.width;
                let height = img.height;

                if (width > height) {
                    if (width > maxSize) {
                        height *= maxSize / width;
                        width = maxSize;
                    }
                } else {
                    if (height > maxSize) {
                        width *= maxSize / height;
                        height = maxSize;
                    }
                }

                canvas.width = width;
                canvas.height = height;
                ctx.drawImage(img, 0, 0, width, height);

                

                imgElement.src = canvas.toDataURL('image/jpeg');
                

                imgElement.alt = 'Flight Photo';
                imgElement.style.width = '100%';
                imgElement.style.height = '100%';
                imgElement.style.objectFit = 'cover';
            };
            img.src = event.target.result;
        };

        reader.readAsDataURL(file);
    }
    


    
    createFormattedResultsInfo() {
        const resultsInfo = document.createElement('div');
        resultsInfo.className = 'results-info';
    
        for (const [key, value] of Object.entries(this.flightCategory.results)) {
            if (key !== 'flight_id') {  // Skip the flight_id
                const formattedKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                let formattedValue = value;
                let colorClass = '';
    
                if (typeof value === 'object' && value !== null) {
                    const status = value[`${key}_status`];
                    const numValue = value[`${key}_value`];
                    formattedValue = `${status} ${numValue ? `(${numValue})` : ''}`.trim();
                    colorClass = status.toLowerCase() === 'pass' ? 'passed-value' : 'failed-value';
                }
    
                resultsInfo.innerHTML += `<p>${formattedKey}: <span class="${colorClass}">${formattedValue}</span></p>`;
            }
        }
        return resultsInfo;
    }
    
    
    

    createResultsInfo() {
        const resultsInfo = document.createElement('div');
        resultsInfo.className = 'results-info';

        for (const [key, value] of Object.entries(this.flightCategory.results)) {
            resultsInfo.innerHTML += `<br>${key}: ${value}`;
        }
        return resultsInfo;
    }
}

class TowerFlightDisplay extends FlightDisplay {
    constructor(flightCategory, fileMap, constituents = []) {
        super(flightCategory, fileMap); // Pass fileMap to super constructor
        this.constituents = constituents;
    }

    createDOMElement() {
        const towerFlightItem = super.createDOMElement();
        towerFlightItem.classList.add('tower-flight');
        
        const constituentsContainer = this.createConstituentsContainer();
        towerFlightItem.appendChild(constituentsContainer);
        
        return towerFlightItem;
    }

    createConstituentsContainer() {
        const container = document.createElement('div');
        container.className = 'constituents-container collapsed';
        
        const toggleButton = document.createElement('button');
        toggleButton.textContent = 'Show Constituents';
        toggleButton.addEventListener('click', () => this.toggleConstituents(container, toggleButton));
        
        container.appendChild(toggleButton);
        
        this.constituents.forEach(constituent => {
            const constituentDisplay = new FlightDisplay(constituent, this.fileMap);
            container.appendChild(constituentDisplay.createDOMElement());
        });
        
        return container;
    }

    toggleConstituents(container, button) {
        container.classList.toggle('collapsed');
        button.textContent = container.classList.contains('collapsed') ? 'Show Constituents' : 'Hide Constituents';
    }
}


function displayFlightGrid(flightAnalysisResult) {
    siteFlightSummary = flightAnalysisResult;
    const flightGrid = document.getElementById('flightGrid');
    flightGrid.innerHTML = '';

    for (const [siteId, siteInspection] of Object.entries(flightAnalysisResult.sites)) {
        const siteDiv = document.createElement('div');
        siteDiv.className = 'site-container';
        siteDiv.innerHTML = `<h2>Site ID: ${siteId}</h2>`;

        for (const [categoryName, flightCategory] of Object.entries(siteInspection.flight_categories)) {
            let flightDisplay;
            if (categoryName.toLowerCase().includes('tower')) {
                const constituents = flightCategory.flights.filter(flight => 
                    /^orbit|ascent|descent|transition/i.test(flight.flight_name)
                );
                flightDisplay = new TowerFlightDisplay(flightCategory, fileMap, constituents);
            } else {
                flightDisplay = new FlightDisplay(flightCategory, fileMap);
            }
            siteDiv.appendChild(flightDisplay.createDOMElement());
        }

        flightGrid.appendChild(siteDiv);
    }
}



import JSZip from 'jszip';

async function moveToFolders(siteFlightSummary, fileMap) {
    const zip = new JSZip();

    try {
        for (const site of Object.values(siteFlightSummary.sites)) {
            for (const flight of site.flights) {
                const flightFolder = zip.folder(flight.flight_name);

                for (const uniqueIdentifier of flight['unique identifiers in flight']) {
                    const file = fileMap.get(uniqueIdentifier);
                    if (file) {
                        const newFileName = uniqueIdentifier + '.' + file.name.split('.').pop();
                        const arrayBuffer = await file.arrayBuffer();
                        flightFolder.file(newFileName, arrayBuffer);
                    }
                }
            }
        }

        const content = await zip.generateAsync({type: "blob"});
        const url = URL.createObjectURL(content);
        const link = document.createElement('a');
        link.href = url;
        link.download = "organized_flights.zip";
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        alert("Zip file with organized folders has been created and download started!");
    } catch (error) {
        console.error('Error creating zip file:', error);
        alert("An error occurred while creating the zip file. Please check the console for details.");
    }
}


async function moveFile(folderHandle, file, uniqueIdentifier, retries = 3) {
    for (let i = 0; i < retries; i++) {
        try {
            // Use the unique identifier as the new file name
            const newFileName = uniqueIdentifier + '.' + file.name.split('.').pop();
            const newFileHandle = await folderHandle.getFileHandle(newFileName, { create: true });
            const writable = await newFileHandle.createWritable();
            await writable.write(file);
            await writable.close();
            console.log(`Moved and renamed file: ${file.name} to ${newFileName} and moved to folder: ${folderHandle.name}`);
            return;
        } catch (error) {
            console.warn(`Error moving file ${file.name}, attempt ${i + 1}:`, error);

            // Check for storage quota error
            if (error.name === 'QuotaExceededError') {
                alert("Error: Not enough disk space. Please free up some space and try again.");
                throw error; // Stop further attempts
            }

            if (i === retries - 1) throw error; // Re-throw if it's the last retry
            await new Promise(resolve => setTimeout(resolve, 1000));
        }
    }
}






function updateUIForProcessing(isProcessing) {
    document.getElementById('fileInput').disabled = isProcessing;
    document.getElementById('loadingView').style.display = isProcessing ? 'block' : 'none';
    document.getElementById('resultsView').style.display = isProcessing ? 'none' : 'block';
}

function handleErrors(error) {
    console.error('An error occurred:', error);
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = `An error occurred: ${error.message}. Please try again.`;
    document.body.appendChild(errorDiv);
}

function updateProgressBar(processed, total) {
    const percentage = (processed / total) * 100;
    document.querySelector('.loading-bar-progress').style.width = `${percentage}%`;
    document.getElementById('loadingStatus').textContent = `Processed ${processed} of ${total} files`;
}

export { 
    
    FlightDisplay, 
    TowerFlightDisplay, 
    displayFlightGrid, 
    updateUIForProcessing, 
    handleErrors, 
    updateProgressBar,
    moveToFolders
};
