# Concepts and Details

## Logical graphs and workflows
A DALiuGE logical graph is representing a computational workflow, where nodes are alternating data and application components. Data components are consumed and produced by applications. Edges are representing  events allowing the graph to be executed and also representing the dependencies. Logical graphs can be constructed using the [EAGLE](https://eagle-dlg.readthedocs.io) visual graph editor and are stored and distributed as JSON files.

## Graph components
Each graph component (application and data) contains a description of a Python object, which will be instantiated at run-time by the DALiuGE execution engine. Those objects, in general, have a payload which is the actual application or data, respectively. We call these object Drops. Component descriptions are essentially JSON structured versions of the code documentation on a class, method and function level.

## Palettes
A DALiuGE palette is a collection of such component descriptions typically covering a Python package. That means that all methods and functions of such a package are in a single palette. When constructing a logical graph with EAGLE, users are dragging components from one or multiple palettes into the canvas and connect them. The component descriptions also aid EAGLE to check whether such connections are valid.

## Palette generation
Palettes can be generated manually using EAGLE, but much more conveniently they can be generated using the `dlg_paletteGen` tool. The tool takes the code directory given as an input parameter and uses [doxygen](https://doxygen.nl) to generate an intermediate XML file. That XML file in turn is then parsed and interpreted to generate the palette and at the end written to a JSON palette file also specified on the command line. Since doxygen is used as the code parser it is possible to use all the more advanced doxygen features. 

For dedicated DALiuGE components it is possible to use [custom doxygen tagging](https://daliuge.readthedocs.io/en/latest/development/app_development/eagle_app_integration.html#component-doxygen-markup-guide) to inform the tool. This used to be the standard way of describing components for DALiuGE. We have then extended the tool to use information extracted by doxygen for arbitrary packages. This turned out to work pretty well and in general all the functions and methods are directly available from the generated palette. The quality of the extracted component descriptions is obviously fully depended on what is available in the code. In particular any description of function arguments and keywords, or the function description itself needs to be in the code. If it is not, the component is still available, but without any hint what it is doing, or the meaning of the arguments and keywords.

Fortunately there are good coding standards for Python and C/C++ to guide developers to produce good and useful in-line documentation. For Python code the `dlg_paletteGen` tool supports Google, rEST and Numpy styles in order to match the identified arguments and keywords to documentation strings. In addition the tool uses Python type hints, if available, to fix the types of arguments and keywords as well as the return values. This in turn is used by EAGLE to check the validity of edges drawn by users when creating a logical graph. 

-- To be continued ---
