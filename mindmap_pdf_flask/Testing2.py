import os
import webbrowser
import time
import random
from pyvis.network import Network

def make_mind_map(topics, edges):

    # Define screen size (matches Pyvis canvas)
    screen_width = 1920  # Example: Full HD width
    screen_height = 1080  # Example: Full HD height

    # Percentage-based spacing (8% of screen width/height for padding)
    spacing_x = int(screen_width * 0.08)
    spacing_y = int(screen_height * 0.08)

    # Define bounding box for node placement
    x_min, x_max = -screen_width // 4, screen_width // 4
    y_min, y_max = -screen_height // 4, screen_height // 4

    # Create a network graph with editable nodes
    net = Network(notebook=True, directed=False, height=f"{screen_height}px", width=f"{screen_width}px", bgcolor="#ffffff",
                  font_color="black")


    # Generate positions dynamically using percentage-based spacing
    def generate_positions(num_nodes):
        positions = {}
        attempts = 0
        max_attempts = 2000  # Allow more iterations for better packing
        while len(positions) < num_nodes and attempts < max_attempts:
            x = random.randint(x_min, x_max)
            y = random.randint(y_min, y_max)

            topic = list(topics.keys())[len(positions)]

            # Ensure new position isn't too close to existing nodes
            too_close = any(
                (abs(x - px) < spacing_x and abs(y - py) < spacing_y)
                for (px, py) in positions.values()
            )

            if not too_close:
                positions[topic] = (x, y)

            attempts += 1

        return positions


    # Generate scalable, non-overlapping positions
    positions = generate_positions(len(topics))

    # Add initial nodes
    # Add initial nodes
    # Add initial nodes without truncation
    for topic, description in topics.items():
        if len(topic) > 100:
            modded_topic = topic[:100] + "..."
        else:
            modded_topic = topic
        good_label = f"{modded_topic}\n\n"
        char_index = 0
        description_index = 0
        while True:
            good_label += description[description_index]
            description_index += 1
            if description_index == len(description):
                break
            char_index += 1
            if char_index > 100 and description[description_index] == " ":
                good_label += "\n\n"
                char_index = 0
        x, y = positions[topic]
        net.add_node(
            topic,
            label=good_label,
            shape="box",
            font={"size": 12, "align": "center"},
            size=max(50, len(description) * 1.2),
            x=x, y=y,
            physics=False
        )

    for edge in edges:
        net.add_edge(*edge)

    # ✅ Inject JavaScript for Editing and Adding Nodes
    edit_script = """
    <script type="text/javascript">
        var editMode = false;

        function toggleEditMode() {
            editMode = !editMode;
            document.getElementById("editButton").innerText = editMode ? "Disable Text Edit" : "Enable Text Edit";
        }

        function attachEditEvent(network) {
            network.on("click", function(params) {
                if (editMode && params.nodes.length > 0) {
                    var nodeId = params.nodes[0];
                    var nodeLabel = network.body.data.nodes.get(nodeId).label;

                    var labelParts = nodeLabel.split("\\n\\n");
                    var currentTitle = labelParts.length > 0 ? labelParts[0] : nodeLabel;
                    var currentDescription = labelParts.length > 1 ? labelParts[1] : "";

                    var newTitle = prompt("Edit topic title:", currentTitle);
                    if (newTitle !== null && newTitle.trim() !== "") {
                        var newDescription = prompt("Edit description:", currentDescription);
                        if (newDescription !== null) {
                            var newLabel = newTitle + "\\n\\n" + newDescription;
                            network.body.data.nodes.update({id: nodeId, label: newLabel});
                        }
                    }
                }
            });
        }

    document.addEventListener("DOMContentLoaded", function() {
        attachEditEvent(network);

        // Button container for alignment
        var buttonContainer = document.createElement("div");
        buttonContainer.style.position = "absolute";
        buttonContainer.style.top = "5vh";  // Adjusted down for alignment
        buttonContainer.style.right = "1vh";
        buttonContainer.style.display = "flex";
        buttonContainer.style.alignItems = "center";
        buttonContainer.style.gap = "1vh";
        buttonContainer.style.zIndex = "100";

        // "Edit Mode" button (styled like built-in buttons)
        var editButton = document.createElement("button");
        editButton.innerHTML = "Enable Text Edit";  // Default state
        editButton.id = "editButton";
        editButton.style.background = "white";
        editButton.style.border = "2px solid #4CAF50";
        editButton.style.color = "#4CAF50";
        editButton.style.padding = "6px 12px";
        editButton.style.borderRadius = "20px";
        editButton.style.fontSize = "14px";
        editButton.style.cursor = "pointer";
        editButton.style.display = "flex";
        editButton.style.alignItems = "center";
        editButton.style.fontWeight = "bold";
        editButton.onmouseover = function() { editButton.style.background = "#E8F5E9"; };
        editButton.onmouseout = function() { editButton.style.background = "white"; };
        editButton.onclick = toggleEditMode;

        // Add buttons to container
        buttonContainer.appendChild(editButton);

        // Add container to body
        document.body.appendChild(buttonContainer);
        document.body.style.overflow = "hidden";  // Prevent scrolling
    });



    </script>
    """
    # Inject JavaScript and Generate the File...
    # (Same as before, adding `edit_script` to the HTML) 🚀

    # Inject JavaScript into the Pyvis HTML
    net.set_options('''
    {
      "physics": {
        "enabled": false
      },
      "interaction": {
        "dragNodes": true,
        "hover": true
      },
      "manipulation": {
        "enabled": true
      },
      "nodes": {
        "borderWidth": 2,
        "shape": "box",
        "font": {"size": 12},
        "margin": 8
      },
      "edges": {
        "smooth": {
          "type": "dynamic"
        }
      }
    }
    ''')

    # Ensure "uploads" is inside static (where it's located in your project)
    base_dir = os.path.dirname(os.path.abspath(__file__))  # Get current script's directory
    mind_map_folder = os.path.join(base_dir, "static", "mind_map_folder")  # Correct path

    # Make sure the folder exists
    os.makedirs(mind_map_folder, exist_ok=True)

    # Save mind_map.html inside the correct uploads folder
    filename = os.path.join(mind_map_folder, "mind_map.html")

    # Generate the mind map
    net.write_html(filename)  # ✅ Now saved inside static/uploads/

    with open(filename, "r+", encoding="utf-8") as file:
        content = file.read()
        content = content.replace("</body>", edit_script + "</body>")
        file.seek(0)
        file.write(content)
        file.truncate()
