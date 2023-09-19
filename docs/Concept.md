# Concepts and Details

## Logical graphs and workflows
A DALiuGE logical graph is representing a computational workflow, where nodes are alternating data and application components. Data components are consumed and produced by applications. Edges are representing events allowing the graph to be executed and also representing the dependencies. Logical graphs can be constructed using the [EAGLE](https://eagle-dlg.readthedocs.io) visual graph editor and are stored and distributed as JSON files.

## Graph components
Each graph component (application and data) contains a description of a Python object, which will be instantiated at run-time by the DALiuGE execution engine. These python objects, in general, have a payload which is the actual executable application or data, respectively. We call these objects Drops. Component descriptions are essentially JSON structured versions of the code documentation on a class, method or function level.

## Palettes
A DALiuGE palette is a collection of such JSON component descriptions typically covering a Python package. That means that all methods and functions of such a package are in a single palette. When constructing a logical graph with EAGLE, users are dragging components from one or multiple palettes into the canvas and connect them. The component descriptions also aid EAGLE to check whether such connections are valid. 

*Note:* While DALiuGE graph components are bound to be written in Python, these components are merely wrappers or interfaces around the actual applications. DALiuGE has built-in wrapper components for dedicated pure python, general python functions and methods, C/C++ library, MPI, Bash CLI and docker based applications. The latter are limited to inter-application communication based on files, the others also offer the ability to use memory communications between different applications in a graph.

## Palette generation
Palettes can be generated manually using EAGLE, but much more conveniently they can be generated using the `dlg_paletteGen` tool. The tool supports two main modes of operations, from source code and from an installed module level. In both cases all the details about the actual running code is extracted from that code directly and can thus only be as good as what the developer(s) of that code provided. Thus the quality of the extracted component descriptions is obviously fully depended on what is available in the code. In particular any description of function arguments and keywords, or the function description itself needs to be in the code. If it is not, the component is still available, but without any hint what it is doing, or the documentation of the arguments and keywords.

Fortunately there are good coding standards for Python and C/C++ to guide developers to produce good and useful in-line documentation. For Python code the `dlg_paletteGen` tool supports Google, rEST and Numpy as well as the domain specific casatask style in order to match the identified arguments and keywords to documentation strings. In addition the tool uses Python introspection (*inspect* module) and Python type hints, if available, to fix the types of arguments and keywords as well as the return values. This type information in turn is used by EAGLE to check the validity of edges drawn by users when creating a logical graph. 

### Module inspection palette generation
This mode enables to extract component descriptions for almost any installed python module directly. This is extremely powerful and totally generic: If the code can be run in your python environment, `DALiuGE` can use it as well! In most cases it will provide a very acurate reflection of the module/package and does not require to write any special code or change any code at all. Palette generation for packages even as big as the whole of [astropy](https://www.astropy.org) or [numpy](https://numpy.org) takes only a few seconds, but generates very big palettes with thousands of components, or alternatively, a whole set of sub-module level palettes, when using the `-S` (`--split`) command line switch. The extraction also supports PyBind11 modules containing virtually no Python code at all.

### Source code palette generation
This was the original approach taken by `dlg_paletteGen`. It takes a code source directory given as an input parameter, `idir` and uses [doxygen](https://doxygen.nl) to generate an intermediate XML file. That XML file in turn is then parsed and interpreted to generate the palette and at the end written to a JSON palette file specified on the command line as `ofile`. Since doxygen is used as the code parser it is possible to use all the more advanced doxygen features. 

For dedicated DALiuGE components it is possible to use [custom doxygen tagging](https://daliuge.readthedocs.io/en/latest/development/app_development/eagle_app_integration.html#component-doxygen-markup-guide) to inform the tool.

## Component types
The tool supports components derived from a number of Python types:

   * Classes
   * Methods (class member functions)
   * Plain functions (not associated to any class)

### Classes and Methods
In practice, during execution, the engine has to deal with objects and not classes. Thus a component representing a class (e.g. *DummyClass*) is actually exposing the initializer method of the *DummyClass* (usually \_\_init\_\_ or \_\_call\_\_). This allows to initialize an object by placing the initializer component on the graph and then connect any of the class methods to it, where required. In order to aid this, the *self* argument of the initializer method is assigned to an output port of the associated component and the *self* argument of all other class methods is assigned to an input port of those components. The type of those ports is set to *Object.DummyClass* and that allows EAGLE to check and enforce valid connections. EAGLE users are thus able to construct object oriented graphs without writing a single line of code. 

*NOTE:* dlg_paletteGen does not expose any *private* functions and methods starting with '\_', except for the initializers \_\_init\_\_ and \_\_call\_\_.

### Plain Functions
These are somewhat simpler than the classes and methods and are typically stand-alone functions contained in a set of files.

## Known limitations
The support for direct module inspection was introduced in release 0.2.0 only and is still regarded experimental. In practice dlg_paletteGen enables the usage of a very big pool of Python software for the DALiuGE system. There are a couple of notable exceptions:

  * Built-in functions
  * Pure C or other language extensions, which are exposed in a similar way as built-in functions

The reason for this limitation comes from an internal Python limitation that does not allow to fully inspect such functions and thus the actual detailed signature of such functions is hidden to the Python interpreter. The behavior of python did change significantly between python3.8 and python3.10, but there are still limitations. Some larger scale packages, e.g. [astropy](https://www.astropy.org) or [numpy](https://numpy.org) are using a mixture between pure C extensions, wrapped C code and plain Python code, thus some of the components might show up in a somewhat limited way. We will continue to work in trying to remove these limitations and would appreciate feedback for packages, which experience issues.