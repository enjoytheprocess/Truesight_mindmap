// static/js/mindmap.js

$(document).ready(function () {
    // Text selection logic
    $('#pdf-text-container').on('mouseup', function () {
        const selectedText = window.getSelection().toString().trim();
        $('#selected-phrase').val(selectedText);
    });

    // Add explanation button
    $('#add-explanation-btn').on('click', function () {
        const phrase = $('#selected-phrase').val();
        const explanationText = $('#explanation-text').val().trim();

        if (!phrase) {
            alert("Please select a phrase in the text first.");
            return;
        }

        if (!explanationText) {
            alert("Please enter an explanation.");
            return;
        }

        // Send POST request to add explanation
        $.ajax({
            url: '/add_explanation',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                phrase: phrase,
                explanationText: explanationText
            }),
            success: function (response) {
                if (response.success) {
                    $('#explanation-text').val('');
                    alert('Explanation added!');
                    loadMindMap();
                }
            },
            error: function () {
                alert('Error adding explanation.');
            }
        });
    });

    // Initialize mind map on load
    loadMindMap();

    function loadMindMap() {
        $.get('/get_explanations', function (data) {
            renderMindMap(data);
        });
    }

    function renderMindMap(explanations) {
        // Create a jsMind-compatible JSON
        const mindData = {
            "meta": {
                "name": "MindMapPDF",
                "author": "You",
                "version": "1.0"
            },
            "format": "node_array",
            "data": []
        };

        // Root node
        mindData.data.push({
            "id": "root",
            "isroot": true,
            "topic": "PDF Explanations"
        });

        // Each explanation becomes a child
        explanations.forEach(exp => {
            mindData.data.push({
                "id": "exp_" + exp.id,
                "parentid": "root",
                "topic": `${exp.phrase} - ${exp.text}`
            });
        });

        // Clear or re-init the mind map
        if (window.jm) {
            window.jm.destroy();
        }

        const options = {
            container: 'jsmind-container',
            editable: false,
            theme: 'primary'
        };
        window.jm = new jsMind(options);
        window.jm.show(mindData);
    }
}
);
