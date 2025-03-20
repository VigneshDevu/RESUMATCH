/*
function uploadResume(){
    let fileInput = 
    document.getElementById("resume");
    let file = fileInput.files[0];

    if(!file){
        document.getElementById("status").innerText = "No file selected";
        return;
    }
    let formData = new FormData();
    formData.append("resume",file);

    fetch("http://127.0.0.1:5000/upload",{
        method: "POST",
        body: formData
    })
    .then(response=> response.text())
    .then(data =>{
        document.getElementById('status').innerText = data;
    })
    .catch(error => {
        console.error("Error:",error);
        document.getElementById("status").innerText="upload failed";
    });
}///



document.getElementById('upload-form').addEventListener('submit', function(event) {
    event.preventDefault();

    let fileInput = document.getElementById('file-input');
    let formData = new FormData();
    
    if (!fileInput.files.length) {
        document.getElementById('message').innerText = "Please select a file!";
        return;
    }

    formData.append('file', fileInput.files[0]);  // ✅ Ensure key is 'file'

    fetch('http://127.0.0.1:5000/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('message').innerText = data.message;
    })
    .catch(error => {
        console.error("Error:", error);
        document.getElementById('message').innerText = "Upload failed!";
    });
});
*/
/*this is latest code
document.getElementById('upload-form').addEventListener('submit', function(event) {
    event.preventDefault();

    let fileInput = document.getElementById('file-input');
    let formData = new FormData();

    if (!fileInput.files.length) {
        document.getElementById('upload-message').innerText = "Please select a file!";
        return;
    }

    formData.append('file', fileInput.files[0]);  // ✅ Ensure key is 'file'

    fetch("http://127.0.0.1:5000/upload", {
        method: "POST",
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('upload-message').innerText = data.message;
    })
    .catch(error => {
        console.error("Error uploading file:", error);
        document.getElementById('upload-message').innerText = "Upload failed!";
    });
});
*/// Handle resume upload
document.getElementById('upload-form').addEventListener('submit', function(event) {
    event.preventDefault();

    let fileInput = document.getElementById('file-input');
    let formData = new FormData();

    if (!fileInput.files.length) {
        document.getElementById('upload-message').innerText = "Please select a file!";
        return;
    }

    formData.append('file', fileInput.files[0]);  // ✅ Ensure key is 'file'

    fetch("http://127.0.0.1:5000/upload", {
        method: "POST",
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('upload-message').innerText = data.message;
    })
    .catch(error => {
        console.error("Error uploading file:", error);
        document.getElementById('upload-message').innerText = "Upload failed!";
    });
});

// Handle job description input and ranking resumes
function matchResumes() {
    let jobDescription = document.getElementById("job-description").value;

    if (!jobDescription) {
        alert("Please enter a job description!");
        return;
    }

    fetch("http://127.0.0.1:5000/match", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ "job_description": jobDescription })
    })
    .then(response => response.json())
    .then(data => {
        if (data.candidates) {
            displayResults(data.candidates);
        } else {
            document.getElementById("results").innerText = "No matching candidates found.";
        }
    })
    .catch(error => console.error("Error:", error));
}

function displayResults(candidates) {
    let resultsDiv = document.getElementById("results");
    resultsDiv.innerHTML = ""; // Clear previous results

    candidates.forEach(candidate => {
        let candidateDiv = document.createElement("div");
        candidateDiv.innerHTML = `<strong>${candidate.Name}</strong> - ${candidate.Email} - ${candidate.Phone} <br> 
                                  Skills: ${candidate.Skills} <br> 
                                  <strong>Match Score:</strong> ${Math.round(candidate["Match Score"] * 100)}% <hr>`;
        resultsDiv.appendChild(candidateDiv);
    });
}
