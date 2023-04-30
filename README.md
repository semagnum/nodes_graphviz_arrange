# Arrange Nodes via Graphviz

## Overview

This is an add-on for Blender 3.5+ that uses the free, open-source [Graphviz](http://graphviz.org/) (a.k.a. `dot`) to automatically arrange nodes in a nice-looking, easy-to-read way:

![(Screencast of Arrange Nodes via Graphviz)](https://github.com/tachimarten/nodes-graphviz-arrange/raw/main/GraphvizScreencast.gif)

Compared to the built-in [Node Arrange] add-on, Arrange Nodes via Graphviz has the following advantages:

* Node Arrange has the tendency to place nodes on top of one another and requires manual margin adjustment to avoid this. Arrange Nodes via Graphviz never places nodes on top of one another.

* Node Arrange will freely place wires underneath nodes, which is hard to read. By contrast, Arrange Nodes via Graphviz inserts and removes [reroute nodes] as necessary in order to route wires around nodes.

  - *Inserting reroute nodes is very time-consuming to do by hand. Arrange Nodes via Graphviz manages them completely automatically.*

* Graphviz tries to place nodes to minimize crossed wires, which can be hard to read. Node Arrange doesn't try to avoid wire crossings.

* Arrange Nodes via Graphviz places nodes so that connected input and output sockets are close to one another as possible, in order to make the flow easy to read. Node Arrange aligns the top edges of nodes vertically, which is usually less readable.

* Node Arrange has inconsistent vertical spacing between nodes. Arrange Nodes via Graphviz's spacing is generally consistent.

* Node Arrange tends to place disconnected nodes far away from the main node graph, which makes it easy to lose them; Arrange Nodes via Graphviz doesn't do this.

* Arrange Nodes via Graphviz tends to center nodes in the middle of the canvas, while Node Arrange lines them up along the top. Centering the nodes looks nicer.

Arrange Nodes via Graphviz works with shader, geometry, and compositing nodes. The spacing between nodes is customizable to your liking.

## Installation

To use Arrange Nodes via Graphviz, you'll first need to install the free, open-source Graphviz software:

* On Windows, you can install it from [http://graphviz.org/](http://graphviz.org/). The EXE installer package is recommended, as this package allows Arrange Nodes via Graphviz to automatically find the program. (The ZIP archive will work too, but you'll have to manually tell this add-on where to find `dot.exe`.)

* On macOS, you can use [Homebrew](https://brew.sh/) and `brew install graphviz`. Arrange Nodes via Graphviz should automatically be able to find the `dot` program after installing it this way. If you install Graphviz.app via MacPorts, you may need to manually tell Arrange Nodes via Graphviz where to find the `dot` program.

* On Linux, you can install Graphviz through your OS's package manager. Like macOS, Arrange Nodes via Graphviz should automatically be able to find the `dot` program after installing it this way.

After installing Graphviz, clone or download this repository somewhere on your disk. Then, in Blender, choose Edit → Preferences, select "Add-ons" on the left, click the "Install…" button, and pick `nodes_graphviz_arrange.py`. Then click the check mark next to "Node: Arrange Nodes via Graphviz".

At this point, you need to ensure that the "`dot` Tool Location" box in the add-on preferences (now visible right underneath "Node: Arrange Nodes via Graphviz") isn't empty. If it is empty, ensure that Graphviz is installed via one of the methods above, and then click "Find Graphviz Automatically". If the "`dot` Tool Location" box is still empty even after clicking that button, then click the 📁 folder icon to the right of it, and navigate to `dot.exe` (on Windows) or `dot` (on macOS and Linux).

## Usage

Whenever you're editing a node tree (whether shader, geometry, or compositor), you can select the Node → Arrange Nodes via Graphviz menu item to automatically arrange the nodes. This operation can be undone as expected. Note that any reroute nodes you manually added will be deleted as part of the operation, as Graphviz manages reroute nodes itself in order to create the most aesthetically pleasing result.

You can also arrange the nodes inside a node group. To do so, simply double-click the node group to inspect it, and then choose Node → Arrange Nodes via Graphviz as usual.

You may wish to quickly arrange nodes as part of your workflow, without having to access the menu item. To do so, you can press F3, type "graphviz", and then press Enter to accept the completion. Then, when you press F3 again, Arrange Nodes via Graphviz will be automatically selected, so you can effectively rearrange nodes by pressing F3 and then Enter.

As an added feature, holding Shift while selecting "Arrange Nodes via Graphviz" renders the node tree to a PDF file and opens that PDF in your system's default PDF viewer. This feature is mostly for debugging the addon, but it may occasionally be useful on its own. Please note that parts of each node may be missing in the PDF, as Blender's node implementations really only expect to be drawing to the screen.

## License

Arrange Nodes via Graphviz is licensed under the Apache 2.0 license. See `LICENSE` for more details.

[Node Arrange]: https://docs.blender.org/manual/en/latest/addons/node/node_arrange.html

[reroute nodes]: https://docs.blender.org/manual/en/latest/interface/controls/nodes/reroute.html
