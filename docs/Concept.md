# Concepts and Details

## Logical graphs and workflows
A DALiuGE logical graph is representing a computational workflow, where nodes are alternating data and application components. Data components are consumed and produced by applications. Edges are representing  events allowing the graph to be executed and also representing the dependencies. Logical graphs can be constructed using the [EAGLE](https://eagle-dlg.readthedocs.io) visual graph editor and are stored and distributed as JSON files.

## Graph components
Each graph component (application and data) contains a description of a Python object, which will be instantiated at run-time by the DALiuGE execution engine. Those objects, in general, have a payload which is the actual executable application or data, respectively. We call these object Drops. Component descriptions are essentially JSON structured versions of the code documentation on a class, method and function level.

## Palettes
A DALiuGE palette is a collection of such JSON component descriptions typically covering a Python package. That means that all methods and functions of such a package are in a single palette. When constructing a logical graph with EAGLE, users are dragging components from one or multiple palettes into the canvas and connect them. The component descriptions also aid EAGLE to check whether such connections are valid.

## Palette generation
Palettes can be generated manually using EAGLE, but much more conveniently they can be generated using the `dlg_paletteGen` tool. The tool takes the code directory given as an input parameter (*idir*) and uses [doxygen](https://doxygen.nl) to generate an intermediate XML file. That XML file in turn is then parsed and interpreted to generate the palette and at the end written to a JSON palette file also specified on the command line (*ofile*). Since doxygen is used as the code parser it is possible to use all the more advanced doxygen features. 

For dedicated DALiuGE components it is possible to use [custom doxygen tagging](https://daliuge.readthedocs.io/en/latest/development/app_development/eagle_app_integration.html#component-doxygen-markup-guide) to inform the tool. This used to be the standard way of describing components for DALiuGE. We have then extended the tool to use information extracted by doxygen for arbitrary packages. This turned out to work pretty well and in general all the functions and methods are directly available from the generated palette. The quality of the extracted component descriptions is obviously fully depended on what is available in the code. In particular any description of function arguments and keywords, or the function description itself needs to be in the code. If it is not, the component is still available, but without any hint what it is doing, or the meaning of the arguments and keywords.

Fortunately there are good coding standards for Python and C/C++ to guide developers to produce good and useful in-line documentation. For Python code the `dlg_paletteGen` tool supports Google, rEST and Numpy as well as the domain specific casatask style in order to match the identified arguments and keywords to documentation strings. In addition the tool uses Python introspection (*inspect* module) and Python type hints, if available, to fix the types of arguments and keywords as well as the return values. This information in turn is used by EAGLE to check the validity of edges drawn by users when creating a logical graph. 

In practice dlg_paletteGen enables the usage of a very big pool of Python software for the DALiuGE system. There are a couple of notable exceptions:

  * Built-in functions
  * Pure C or other language extensions, which are exposed in a similar way as built-in functions

The reason for this limitation comes from an internal Python limitation that does not allow to inspect such functions and thus the actual detailed signature of such functions is unknown to the Python interpreter. Some larger scale packages, e.g. *numpy* or *AstroPy* are using a mixture between pure C extensions, wrapped C code and plain Python code, thus the latter two will appear as components, the first ones not.

## Component Types
The tool supports components derived from a number of Python types:

   * Classes
   * Methods (class member functions)
   * Plain functions (not associated to any class)

### Classes and Methods
In practice, during execution, the engine has to deal with objects and not classes. Thus a component representing a class (e.g. *DummyClass*) is actually exposing the initializer method of the *DummyClass* (usually \_\_init\_\_ or \_\_call\_\_). This allows to initialize an object by placing the initializer component on the graph and then connect any of the class methods to it, where required. In order to aid this, the *self* argument of the initializer method is assigned to an output port of the associated component and the *self* argument of all other class methods is assigned to an input port of those components. The type of those ports is set to *Object.DummyClass* and that allows EAGLE to check and enforce valid connections. This allows EAGLE users to construct object oriented graphs without writing a line of code.

### Plain Functions
These are somewhat simpler than the classes and methods and are typically stand-alone functions contained in a set of files.