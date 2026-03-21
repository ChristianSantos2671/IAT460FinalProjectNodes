\# IAT 460 Final Project: Aperiodic Tiling Nodes for ComfyUI



This repository contains a suite of custom \*\*ComfyUI nodes\*\* designed to generate, process, and render aperiodic "Hat" tilings. These nodes are a direct port of the original `AperiodicTiles` Python scripts, allowing for a modular, node-based workflow within the ComfyUI interface.



\## 🚀 Installation



1\.  Navigate to your ComfyUI installation's `custom\_nodes` directory:

&#x20;   ```bash

&#x20;   cd ComfyUI/custom\_nodes/

&#x20;   ```

2\.  Clone this repository:

&#x20;   ```bash

&#x20;   git clone https://github.com/ChristianSantos2671/IAT460FinalProjectNodes

&#x20;   ```

3\.  Restart ComfyUI. The nodes will appear under the \*\*Aperiodic Tiles\*\* category in the right-click menu.



\---



\## 🧩 Included Nodes



The workflow is split into five distinct stages, mirroring the original logic of the `tile.sh` pipeline:



\### 1. Hat Tiling Generator (`hat\_tiling.py`)

Generates the initial recursive geometry of the Einstein "Hat" monotile.

\* \*\*Input:\*\* `iterations` (integer) – Controls the complexity/depth of the tiling.

\* \*\*Output:\*\* `TILING\_DATA` – Raw coordinate data for the generated tiles.



\### 2. Aperiodic Fill Canvas (`fill\_canvas.py`)

Scales and centers the generated tiles to fit a specific boundary.

\* \*\*Input:\*\* `width`, `height`, `padding`, and `auto\_scale` toggle.

\* \*\*Output:\*\* `CANVAS\_DATA` – Transformed geometry fitted to the canvas dimensions.



\### 3. Assign Tile Heights (`assign\_tile\_heights.py`)

Assigns a numerical height and a corresponding color hex code to each tile.

\* \*\*Input:\*\* `seed` (for deterministic randomness), `min\_h`, `max\_h`, and hue controls.

\* \*\*Output:\*\* `HEIGHT\_DATA` – Geometry data appended with height and color metadata.



\### 4. Render Canvas (Terminal Node) (`render\_canvas.py`)

Generates a full-scale HTML/SVG visualization of the tiling.

\* \*\*Input:\*\* `filename` – The name of the HTML file to be saved.

\* \*\*Action:\*\* Saves the file to the ComfyUI `output` directory.



\### 5. Render Panel (Terminal Node) (`render\_panel.py`)

Isolates specific subsets of tiles for detailed reference or production panels.

\* \*\*Input:\*\* `panel\_id`, `tiles\_per\_panel`, and `filename`.

\* \*\*Action:\*\* Saves an HTML file with specialized labeling for the selected panel.



\---



\## 🛠 Workflow Example



To replicate the original technology stack, connect the nodes in the following sequence:



1\.  \*\*Hat Tiling Generator\*\* (Set iterations to 3 or 4).

2\.  Connect `TILING\_DATA` to \*\*Aperiodic Fill Canvas\*\*.

3\.  Connect `CANVAS\_DATA` to \*\*Assign Tile Heights\*\*.

4\.  Connect `HEIGHT\_DATA` to both \*\*Render Canvas\*\* and \*\*Render Panel\*\*.

5\.  Press \*\*Queue Prompt\*\* to generate the HTML files in your `output/` folder.



\---



\## 📂 Repository Structure



```text

IAT460FinalProjectNodes/

├── \_\_init\_\_.py               # Node registration and mappings

├── hat\_tiling.py             # Geometry generation logic

├── fill\_canvas.py            # Coordinate transformation and centering

├── assign\_tile\_heights.py    # Randomization and color mapping

├── render\_canvas.py          # HTML/SVG output for the full canvas

└── render\_panel.py           # HTML/SVG output for individual panels

```

