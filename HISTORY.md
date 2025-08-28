Changelog
=========


(unreleased)
------------
- Enables LLM docstring generation. [Andreas Wicenec]


0.6.5 (2025-08-21)
------------------
- Release: version 0.6.5 🚀 [Andreas Wicenec]
- Return source code if no documentation is found. [Andreas Wicenec]

  The source code is formatted as a description and
  added to the palette.


0.6.4 (2025-08-20)
------------------
- Release: version 0.6.4 🚀 [Andreas Wicenec]
- Return full description for casa nodes. [Andreas Wicenec]
- Release: version 0.6.3 🚀 [Andreas Wicenec]
- Fix method filtering. [Andreas Wicenec]


0.6.3 (2025-08-13)
------------------
- Release: version 0.6.3 🚀 [Andreas Wicenec]


0.6.2 (2025-08-12)
------------------
- Release: version 0.6.2 🚀 [Andreas Wicenec]
- Added prevent_cycle import option and fixed some tests. [Andreas
  Wicenec]


0.6.1 (2025-08-12)
------------------
- Release: version 0.6.1 🚀 [Andreas Wicenec]
- Fixed issues with tensorflow and jax. [Andreas Wicenec]
- Enable running paletteGen on itself and use in graph. [Andreas
  Wicenec]
- Release: version 0.6.0 🚀 [Andreas Wicenec]


0.6.0 (2025-07-16)
------------------
- Release: version 0.6.0 🚀 [Andreas Wicenec]
- Fixed issue with annotation extraction. [Andreas Wicenec]
- Major refactoring to improve code structure. [Andreas Wicenec]

  Also support for additional packages, which caused
  issues.


0.5.5 (2025-07-11)
------------------
- Release: version 0.5.5 🚀 [Andreas Wicenec]
- Merge branch 'DGEN-25' [Andreas Wicenec]
- Fixed formatting. [Andreas Wicenec]


0.5.4 (2025-07-11)
------------------
- Release: version 0.5.4 🚀 [Andreas Wicenec]
- Refactored import logic to handle module retrieval more robustly.
  [Andreas Wicenec]

  Enabled ability to analyze modules and functions
  directly in the interpreter or from an external
  script.
- Fixed final test. [Andreas Wicenec]
- Fixed treating of __init__ descriptions. [Andreas Wicenec]
- Work-around for missing blank line in docstrings. [Andreas Wicenec]
- Fixed self output port. [Andreas Wicenec]
- Numpy seems to have a different number of components on Linux than on
  Mac... [Andreas Wicenec]
- Reformatting to fix linter error. [Andreas Wicenec]


0.5.3 (2025-05-16)
------------------
- Release: version 0.5.3 🚀 [Andreas Wicenec]
- Use return_name from description parser for output_name. [Andreas
  Wicenec]


0.5.2 (2025-04-23)
------------------
- Release: version 0.5.2 🚀 [Andreas Wicenec]
- Removed inconsistency with PyFuncApp. [Andreas Wicenec]


0.5.1 (2025-04-22)
------------------
- Release: version 0.5.1 🚀 [Andreas Wicenec]
- Reverted default types to uppercase. [Andreas Wicenec]


0.5.0 (2025-04-22)
------------------
- Release: version 0.5.0 🚀 [Andreas Wicenec]
- Deleted unused import. [Andreas Wicenec]
- Merge branch 'DGEN-20' [Andreas Wicenec]
- Suggestions implemented; tests fixed. [Andreas Wicenec]
- Applied sourcery corrections. [Andreas Wicenec]
- Aligned palette output with what EAGLE expects. [Andreas Wicenec]
- Release: version 0.4.7 🚀 [Andreas Wicenec]
- Added log_level field to default fields. [Andreas Wicenec]
- Release: version 0.4.6 🚀 [Andreas Wicenec]
- Re-formatting. [Andreas Wicenec]
- Aligned all standard types to Python names. [Andreas Wicenec]
- Categories are now DALiuGEApp and PyFuncApp. [Andreas Wicenec]
- Fixed linting issue. [Andreas Wicenec]
- Added support for PythonFunction category. [Andreas Wicenec]
- Fixes required after merge with master. [Andreas Wicenec]

  Also fixed the make install to be compliant with pep517.
- Re-align missed changes. [Andreas Wicenec]
- Aligned palette output with what EAGLE expects. [Andreas Wicenec]
- Release: version 0.4.7 🚀 [Andreas Wicenec]
- Added log_level field to default fields. [Andreas Wicenec]
- Release: version 0.4.6 🚀 [Andreas Wicenec]
- Re-formatting. [Andreas Wicenec]
- Aligned all standard types to Python names. [Andreas Wicenec]
- Categories are now DALiuGEApp and PyFuncApp. [Andreas Wicenec]
- Fixed linting issue. [Andreas Wicenec]
- Added support for PythonFunction category. [Andreas Wicenec]
- Revert merge. [Andreas Wicenec]
- Merge wirh master. [Andreas Wicenec]
- Re-formatting. [Andreas Wicenec]
- Aligned all standard types to Python names. [Andreas Wicenec]
- Categories are now DALiuGEApp and PyFuncApp. [Andreas Wicenec]
- Fixed linting issue. [Andreas Wicenec]
- Added support for PythonFunction category. [Andreas Wicenec]
- Release: version 0.4.8 🚀 [Andreas Wicenec]
- Fixed linting and test error. [Andreas Wicenec]
- Fixed some edge cases on casa; made shure others are still working.
  [Andreas Wicenec]
- Fix linter issues. [Ryan Bunney]
- Improve robustness of the load_name setting using dir(module). [Ryan
  Bunney]

  This ensures that the load_name is actually found in module.load_name, rather than
  the previous approach which was more of a 'guess'.
- Update naming management to address casa issue. [Ryan Bunney]

  - Use empty string in _get_name() when not a class and doesn't have __name__
  - Use member.__module__ if the name of the member is in the module, rather than appending a duplicate at the end (module.name.name).
  - Use absolute over relative imports for modules.
- Aligned palette output with what EAGLE expects. [Andreas Wicenec]
- Release: version 0.4.7 🚀 [Andreas Wicenec]
- Added log_level field to default fields. [Andreas Wicenec]
- Fixed format issue. [Andreas Wicenec]
- Changed PyFuncApp to PythonFunction. [Andreas Wicenec]
- Merge branch 'casa_incorrect_name_fix' [Andreas Wicenec]
- Suggestions implemented; tests fixed. [Andreas Wicenec]
- Applied sourcery corrections. [Andreas Wicenec]
- Aligned palette output with what EAGLE expects. [Andreas Wicenec]
- Release: version 0.4.7 🚀 [Andreas Wicenec]
- Added log_level field to default fields. [Andreas Wicenec]
- Release: version 0.4.6 🚀 [Andreas Wicenec]
- Re-formatting. [Andreas Wicenec]
- Aligned all standard types to Python names. [Andreas Wicenec]
- Categories are now DALiuGEApp and PyFuncApp. [Andreas Wicenec]
- Fixed linting issue. [Andreas Wicenec]
- Added support for PythonFunction category. [Andreas Wicenec]
- Fixes required after merge with master. [Andreas Wicenec]

  Also fixed the make install to be compliant with pep517.
- Re-align missed changes. [Andreas Wicenec]
- Aligned palette output with what EAGLE expects. [Andreas Wicenec]
- Release: version 0.4.7 🚀 [Andreas Wicenec]
- Added log_level field to default fields. [Andreas Wicenec]
- Release: version 0.4.6 🚀 [Andreas Wicenec]
- Re-formatting. [Andreas Wicenec]
- Aligned all standard types to Python names. [Andreas Wicenec]
- Categories are now DALiuGEApp and PyFuncApp. [Andreas Wicenec]
- Fixed linting issue. [Andreas Wicenec]
- Added support for PythonFunction category. [Andreas Wicenec]
- Revert merge. [Andreas Wicenec]
- Merge wirh master. [Andreas Wicenec]
- Aligned palette output with what EAGLE expects. [Andreas Wicenec]
- Added log_level field to default fields. [Andreas Wicenec]
- Re-formatting. [Andreas Wicenec]
- Aligned all standard types to Python names. [Andreas Wicenec]
- Categories are now DALiuGEApp and PyFuncApp. [Andreas Wicenec]
- Fixed linting issue. [Andreas Wicenec]
- Added support for PythonFunction category. [Andreas Wicenec]
- Aligned palette output with what EAGLE expects. [Andreas Wicenec]


0.4.8 (2025-04-16)
------------------
- Release: version 0.4.8 🚀 [Andreas Wicenec]
- Fixed linting and test error. [Andreas Wicenec]
- Fixed some edge cases on casa; made shure others are still working.
  [Andreas Wicenec]
- Fix linter issues. [Ryan Bunney]
- Improve robustness of the load_name setting using dir(module). [Ryan
  Bunney]

  This ensures that the load_name is actually found in module.load_name, rather than
  the previous approach which was more of a 'guess'.
- Update naming management to address casa issue. [Ryan Bunney]

  - Use empty string in _get_name() when not a class and doesn't have __name__
  - Use member.__module__ if the name of the member is in the module, rather than appending a duplicate at the end (module.name.name).
  - Use absolute over relative imports for modules.


0.4.7 (2025-04-08)
------------------
- Release: version 0.4.7 🚀 [Andreas Wicenec]
- Added log_level field to default fields. [Andreas Wicenec]
- Merge branch 'DGEN-20' [Andreas Wicenec]


0.4.6 (2025-04-02)
------------------
- Release: version 0.4.6 🚀 [Andreas Wicenec]
- Re-formatting. [Andreas Wicenec]
- Aligned all standard types to Python names. [Andreas Wicenec]
- Categories are now DALiuGEApp and PyFuncApp. [Andreas Wicenec]
- Fixed linting issue. [Andreas Wicenec]
- Added support for PythonFunction category. [Andreas Wicenec]


0.4.5 (2025-03-30)
------------------
- Release: version 0.4.5 🚀 [Andreas Wicenec]
- Deal with return values, types and description. [Andreas Wicenec]
- Fixed linting error. [Andreas Wicenec]


0.4.4 (2025-03-30)
------------------
- Release: version 0.4.4 🚀 [Andreas Wicenec]
- Improved help text and CLI parameter handling. [Andreas Wicenec]
- Updated documentation and CLI parameter handling. [Andreas Wicenec]
- Use output file name if provided in module mode. [Andreas Wicenec]


0.4.3 (2025-03-29)
------------------
- Release: version 0.4.3 🚀 [Andreas Wicenec]
- Added importlib.metadata import. [Andreas Wicenec]
- Release: version 0.4.2 🚀 [Andreas Wicenec]


0.4.1 (2025-03-29)
------------------
- Release: version 0.4.1 🚀 [Andreas Wicenec]
- Release: version 0.4.1 🚀 [Andreas Wicenec]
- Release: version 0.4.1 🚀 [Andreas Wicenec]
- Aut-reformat. [Andreas Wicenec]
- Re-format example_rascil. [Andreas Wicenec]
- Removed dependecy from merklelib. [Andreas Wicenec]
- Release: version 0.4.1 🚀 [Andreas Wicenec]
- Merge branch 'DGEN-19' [Andreas Wicenec]
- Fixed tests. [Andreas Wicenec]
- Added output port if return_annotation exists. [Andreas Wicenec]
- Merge branch 'parser_update' into DGEN-19. [Andreas Wicenec]
- Always use type annotations. [Andreas Wicenec]
- Try to get version of module. [Andreas Wicenec]
- Merge pull request #9 from ICRAR/casaDocstring_BugFix. [Ryan Bunney]

  Update self.params created by _process_casa consistent with other docstring types.
- Make the self.params created by _process_casa consistent with other
  docstring types. [Ryan Bunney]
- Release: version 0.4.0 🚀 [Andreas Wicenec]
- Release: version 0.4.0 🚀 [Andreas Wicenec]
- Adjusting tests. [Andreas Wicenec]
- Removed stray debug log. [Andreas Wicenec]
- Fixed some detailed parser issues. [Andreas Wicenec]
- Format and test fix. [Andreas Wicenec]
- Removed commented code. [Andreas Wicenec]
- Enabled support for direct function parsing. [Andreas Wicenec]
- Old code removed. [Andreas Wicenec]
- Fixed recursive behavior. [Andreas Wicenec]
- Updates to improve parameter parsing. [Andreas Wicenec]
- Parser updates to support additional packages. [Andreas Wicenec]
- Formatting changes. [Andreas Wicenec]
- Updated Google and Numpy extraction. [Andreas Wicenec]
- Make colon after Returns optional. [Andreas Wicenec]
- Fixed Google docstring extraction. [Andreas Wicenec]
- Main: Add prerequisites to README.md. [Ryan Bunney]


0.4.0 (2025-02-05)
------------------
- Release: version 0.4.0 🚀 [Andreas Wicenec]
- Merge branch 'parser_update' [Andreas Wicenec]
- Adjusting tests. [Andreas Wicenec]
- Removed stray debug log. [Andreas Wicenec]
- Fixed some detailed parser issues. [Andreas Wicenec]
- Format and test fix. [Andreas Wicenec]
- Removed commented code. [Andreas Wicenec]
- Enabled support for direct function parsing. [Andreas Wicenec]
- Old code removed. [Andreas Wicenec]
- Fixed recursive behavior. [Andreas Wicenec]
- Updates to improve parameter parsing. [Andreas Wicenec]
- Parser updates to support additional packages. [Andreas Wicenec]
- Formatting changes. [Andreas Wicenec]
- Updated Google and Numpy extraction. [Andreas Wicenec]
- Make colon after Returns optional. [Andreas Wicenec]
- Fixed Google docstring extraction. [Andreas Wicenec]


0.3.10 (2024-11-15)
-------------------
- Release: version 0.3.10 🚀 [Ryan Bunney]
- Merge pull request #7 from ICRAR/fix_linting. [Ryan Bunney]

  Fix linting: address failing workflows on github
- Use numpy module len() value reported on CI machines. [Ryan Bunney]
- Formatting. [Ryan Bunney]
- Update tests and None checks to see if this fixes test failures. [Ryan
  Bunney]
- Fix linting: More yaml errors. [Ryan Bunney]
- Fix linting: More yaml errors. [Ryan Bunney]
- Fix linting: Fix yaml error. [Ryan Bunney]
- Fix linting: Update actions to run on all pushes. [Ryan Bunney]
- Fix linting: address failing workflows on github. [Ryan Bunney]


0.3.9 (2024-11-11)
------------------
- Release: version 0.3.9 🚀 [Andreas Wicenec]
- Fixed some import hierarchy issues. [Andreas Wicenec]
- Playning around with recursion issues. [Andreas Wicenec]
- Fixed Numpy doc Returns line treatment. [Andreas Wicenec]
- Release: version 0.3.8 🚀 [Andreas Wicenec]
- Formatting fixed. [Andreas Wicenec]
- Release: version 0.3.8 🚀 [Andreas Wicenec]


0.3.8 (2024-05-28)
------------------
- Release: version 0.3.8 🚀 [Andreas Wicenec]
- Suppress error messages for typing module. [Andreas Wicenec]
- Release: version 0.3.7 🚀 [Andreas Wicenec]
- Removed isort ignore. [Andreas Wicenec]
- More generic handling of module members. [Andreas Wicenec]


0.3.7 (2024-05-28)
------------------
- Release: version 0.3.7 🚀 [Andreas Wicenec]


0.3.6 (2024-04-18)
------------------
- Release: version 0.3.6 🚀 [Andreas Wicenec]
- Fixed value of complex types. [Andreas Wicenec]


0.3.5 (2024-03-25)
------------------
- Release: version 0.3.5 🚀 [Andreas Wicenec]
- Release: version 0.3.4 🚀 [Andreas Wicenec]
- Updated gituhub actions. [Andreas Wicenec]


0.3.4 (2024-03-25)
------------------
- Release: version 0.3.4 🚀 [Andreas Wicenec]
- Fixed linting errors. [Andreas Wicenec]
- Fixed failing tests. [Andreas Wicenec]
- Create PythonMemberFunction and PythonObject. [Andreas Wicenec]
- Release: version 0.3.3 🚀 [Andreas Wicenec]
- Release: version 0.3.3 🚀 [Andreas Wicenec]
- Don't execute windows tests. [Andreas Wicenec]
- Removed dask-ms from requirements. [Andreas Wicenec]
- Removed casatools imports. [Andreas Wicenec]


0.3.3 (2024-03-02)
------------------
- Release: version 0.3.3 🚀 [Andreas Wicenec]
- Bumped to new version of benedict. [Andreas Wicenec]
- Refactoring. [Andreas Wicenec]
- Fixed tests and format. [Andreas Wicenec]
- Updated to python-benedict. [Andreas Wicenec]
- Fixed aoflagger's way of documenting. [Andreas Wicenec]
- Fixed treatment of embedded function parameters. [Andreas Wicenec]


0.3.2 (2023-09-20)
------------------
- Release: version 0.3.2 🚀 [Andreas Wicenec]
- Simplified populateFields, fixed recursion. [Andreas Wicenec]
- Doc updates and fixes for numpy. [Andreas Wicenec]
- Better test coverage, removed stale code. [Andreas Wicenec]
- Addition for tabascal oddities. [Andreas Wicenec]
- Added number of nodes to palette meta. [Andreas Wicenec]


0.3.1 (2023-09-18)
------------------
- Release: version 0.3.1 🚀 [Andreas Wicenec]
- More compliance with OSKAR. [Andreas Wicenec]


0.3.0 (2023-09-17)
------------------
- Release: version 0.3.0 🚀 [Andreas Wicenec]
- Fixed type guessing, added test. [Andreas Wicenec]
- Release: version 0.2.9 🚀 [Andreas Wicenec]
- Fixed type assignments in rascil. [Andreas Wicenec]


0.2.9 (2023-09-14)
------------------
- Release: version 0.2.9 🚀 [Andreas Wicenec]
- Release: version 0.2.8 🚀 [Andreas Wicenec]
- Fixed issues with rascil. [Andreas Wicenec]


0.2.8 (2023-09-14)
------------------
- Release: version 0.2.8 🚀 [Andreas Wicenec]
- Another try fixing decoding. [Andreas Wicenec]
- Try fixing decode error. [Andreas Wicenec]
- Fixed test. [Andreas Wicenec]


0.2.7 (2023-09-12)
------------------
- Release: version 0.2.7 🚀 [Andreas Wicenec]
- Some fixes for radler. [Andreas Wicenec]


0.2.6 (2023-09-12)
------------------
- Release: version 0.2.6 🚀 [Andreas Wicenec]
- Added palette descriptions from modules. [Andreas Wicenec]
- Fixed construct node extraction. [Andreas Wicenec]
- Release: version 0.2.4 🚀 [Andreas Wicenec]
- Updated documentation. [Andreas Wicenec]


0.2.5 (2023-09-12)
------------------
- Release: version 0.2.5 🚀 [Andreas Wicenec]
- Fixed func_name and scipy issues. [Andreas Wicenec]
- Fixed typo. [Andreas Wicenec]


0.2.4 (2023-09-11)
------------------
- Release: version 0.2.4 🚀 [Andreas Wicenec]
- Support for splitting large modules. [Andreas Wicenec]
- Fixed issues treating tabascal package. [Andreas Wicenec]


0.2.3 (2023-09-09)
------------------
- Release: version 0.2.3 🚀 [Andreas Wicenec]
- ESO pyCPL extraction works. [Andreas Wicenec]
- More cases covered in import_using_name. [Andreas Wicenec]
- Fixed a few corner cases in astropy and numpy. [Andreas Wicenec]
- Fixed stray case in numpy. [Andreas Wicenec]
- Removed self argument from __init__ [Andreas Wicenec]


0.2.2 (2023-09-03)
------------------
- Release: version 0.2.2 🚀 [Andreas Wicenec]
- Support for classes added to module mode. [Andreas Wicenec]


0.2.1 (2023-09-01)
------------------
- Release: version 0.2.1 🚀 [Andreas Wicenec]
- Suppress multiplied modules. [Andreas Wicenec]
- Restructuring of code. [Andreas Wicenec]
- Better support for builtin functions. [Andreas Wicenec]
- Updated documentation. [Andreas Wicenec]


0.2.0 (2023-09-01)
------------------
- Release: version 0.2.0 🚀 [Andreas Wicenec]
- Compatibility with python 3.9. [Andreas Wicenec]
- Update requirements.txt. [awicenec]

  added blockdag again.
- Update requirements-test.txt. [awicenec]

  missing stub package added
- Update support_functions.py. [awicenec]

  added required spaces
- Update support_functions.py. [awicenec]

  another type error
- Fixed linting errors. [Andreas Wicenec]
- Added module palette writing. [Andreas Wicenec]
- Added .vscode. [Andreas Wicenec]


0.1.15 (2023-07-18)
-------------------
- Release: version 0.1.15 🚀 [Andreas Wicenec]
- Added direct cli testing. [Andreas Wicenec]
- Brought back the module hook and brief description. [Andreas Wicenec]


0.1.14 (2023-07-18)
-------------------
- Release: version 0.1.14 🚀 [Andreas Wicenec]
- Release: version 0.1.13 🚀 [Andreas Wicenec]
- Fixed casadoc treatment. [Andreas Wicenec]


0.1.13 (2023-07-14)
-------------------
- Release: version 0.1.13 🚀 [Andreas Wicenec]
- Release: version 0.1.10 🚀 [Andreas Wicenec]
- Release: version 0.1.12 🚀 [Andreas Wicenec]
- Final touches. [Andreas Wicenec]


0.1.12 (2023-07-12)
-------------------
- Release: version 0.1.12 🚀 [Andreas Wicenec]
- Added classmethods; fixed google processing for oskar. [Andreas
  Wicenec]


0.1.11 (2023-07-06)
-------------------
- Release: version 0.1.11 🚀 [Andreas Wicenec]
- Fix for missing port definitions. [Andreas Wicenec]


0.1.10 (2023-07-06)
-------------------
- Release: version 0.1.10 🚀 [Andreas Wicenec]
- Merge branch 'dgen-12' [Andreas Wicenec]
- Fixed linting errors. [Andreas Wicenec]
- Finally got this workling again. [Andreas Wicenec]
- Improved modelData section, now includes lastModified etc. [james-
  strauss-uwa]
- Added back the 'tag' functionality where you can filter components by
  a tag specified on the command line. [james-strauss-uwa]
- Re-enabled warning message. [james-strauss-uwa]
- Work-in-progress moving to new format for EAGLE doxygen. [james-
  strauss-uwa]


0.1.9 (2023-07-05)
------------------
- Release: version 0.1.9 🚀 [Andreas Wicenec]
- Added tag filter. [Andreas Wicenec]
- Ignore .vscode dir. [Andreas Wicenec]
- Ignore .vscode. [Andreas Wicenec]
- Added support for constructParam. [Andreas Wicenec]
- Refactored Field into dataclass. [Andreas Wicenec]
- Added recursion into sub-modules. [Andreas Wicenec]
- Initial support for module parsing. [Andreas Wicenec]
- Release: version 0.1.8 🚀 [Andreas Wicenec]
- Doc updates. [Andreas Wicenec]
- Release: version 0.1.8 🚀 [Andreas Wicenec]
- More documentation. [Andreas Wicenec]


0.1.8 (2023-02-01)
------------------
- Release: version 0.1.8 🚀 [Andreas Wicenec]
- Release: version 0.1.7 🚀 [Andreas Wicenec]
- Fixed inconsistency between black and isort. [Andreas Wicenec]
- Release: version 0.1.7 🚀 [Andreas Wicenec]
- Updated links. [Andreas Wicenec]
- Release: version 0.1.7 🚀 [Andreas Wicenec]
- Release: version 0.1.7 🚀 [Andreas Wicenec]


0.1.7 (2023-02-01)
------------------
- Release: version 0.1.7 🚀 [Andreas Wicenec]
- Fixed some import issues. [Andreas Wicenec]
- Fixed problem with check_required_fields_for_category. [Andreas
  Wicenec]
- Merge pull request #3 from ICRAR/dgen-10. [awicenec]

  Dgen 10
- Fixed import of NAME. [Andreas Wicenec]
- Minor format change. [Andreas Wicenec]
- Changed link to documentation. [Andreas Wicenec]
- No real change. [Andreas Wicenec]
- Enabled showing version info. [Andreas Wicenec]
- Release: version 0.1.6 🚀 [Andreas Wicenec]
- Release: version 0.1.6 🚀 [Andreas Wicenec]
- Merge pull request #2 from ICRAR/dgen-1. [awicenec]

  Dgen 1
- Install wheel package. [Andreas Wicenec]
- Big refactoring. [Andreas Wicenec]
- Fixed lint and test. [Andreas Wicenec]
- Mostly done now. [Andreas Wicenec]
- Use XPath to process compounddefs. [Andreas Wicenec]
- Started re-factoring for usage a XPath. [Andreas Wicenec]


0.1.6 (2023-01-13)
------------------
- Release: version 0.1.6 🚀 [Andreas Wicenec]
- Release: version 0.1.5 🚀 [Andreas Wicenec]
- Fixed issue with missing constructs default params. [Andreas Wicenec]


0.1.5 (2022-12-22)
------------------
- Release: version 0.1.5 🚀 [Andreas Wicenec]
- Fixed RASCIL and C style issues. [Andreas Wicenec]
- Fixed issues with RASCIL processing. [Andreas Wicenec]
- Better coverage in rest and eagle. [Andreas Wicenec]
- Renamed test file to example_eagle.py. [Andreas Wicenec]


0.1.4 (2022-12-22)
------------------
- Release: version 0.1.4 🚀 [Andreas Wicenec]
- Added example_rest.py to git. [Andreas Wicenec]
- Added rEST example; code restructuring. [Andreas Wicenec]
- Removed one test and associated code. [Andreas Wicenec]
- Updated documentation. [Andreas Wicenec]


0.1.3 (2022-12-20)
------------------
- Release: version 0.1.3 🚀 [Andreas Wicenec]
- Updated Makefile and gitignore. [Andreas Wicenec]
- Fixed treatment of CASA style docs. [Andreas Wicenec]
- Another typo. [Andreas Wicenec]
- Typo. [Andreas Wicenec]
- Added xsltproc. [Andreas Wicenec]
- Added sudo. [Andreas Wicenec]
- Add doxygen to Linux. [Andreas Wicenec]


0.1.2 (2022-12-19)
------------------
- Release: version 0.1.2 🚀 [Andreas Wicenec]
- Fixed workflow. [Andreas Wicenec]
- Add doxygen to MacOSX. [Andreas Wicenec]
- Adding example data. [Andreas Wicenec]
- Fixed formatting for lint. [Andreas Wicenec]
- Re-factoring of detaileddescription element. [Andreas Wicenec]
- Test coverage increased to 80% [Andreas Wicenec]
- Removed the link to the contributing page. [Andreas Wicenec]
- Changed documentation link. [Andreas Wicenec]
- Changed Containerfile to use Python3.9. [Andreas Wicenec]
- Formatting update. [Andreas Wicenec]
- Small doc update. [Andreas Wicenec]
- Try using prebuild github action. [Andreas Wicenec]
- Removed git again. [Andreas Wicenec]
- Added git to requirements. [Andreas Wicenec]
- Typo. [Andreas Wicenec]
- Changed mkdocs command. [Andreas Wicenec]
- Updated documentation. [Andreas Wicenec]
- Added mkdocs. [Andreas Wicenec]
- Added docs/requirements.txt. [Andreas Wicenec]
- Dded docs and documentation build. [Andreas Wicenec]
- Added first shot of documentation. [Andreas Wicenec]
- Changed Headline. [Andreas Wicenec]
- Updated README. [Andreas Wicenec]
- Updated README. [Andreas Wicenec]
- Added dlg-paletteGen as CLI command. [Andreas Wicenec]
- Badge fix. [awicenec]
- Codecov version update. [Andreas Wicenec]
- Hopefully last action updates. [Andreas Wicenec]
- More action updates. [Andreas Wicenec]
- Updated to new versions of actions. [Andreas Wicenec]
- Release: version 0.1.1 🚀 [Andreas Wicenec]
- Hanged PYPI token name. [Andreas Wicenec]
- Release: version 0.1.1 🚀 [Andreas Wicenec]


0.1.1 (2022-12-15)
------------------
- Release: version 0.1.1 🚀 [Andreas Wicenec]
- Removed initial workflow files. [Andreas Wicenec]
- Release: version 0.1.0 🚀 [Andreas Wicenec]


0.1.0 (2022-12-15)
------------------
- Release: version 0.1.0 🚀 [Andreas Wicenec]
- Fixed incompatibility between isort and black defaults. [Andreas
  Wicenec]
- Fixed E203 formatting hassle. [Andreas Wicenec]
- Fixed the difference between Python3.8 and 3.9. [Andreas Wicenec]
- Fixed additional formatting issues. [Andreas Wicenec]
- Added VERSION file. [Andreas Wicenec]
- Whole code with fmt and mymy fixes. [Andreas Wicenec]
- Renamed to dlg_paletteGen. [Andreas Wicenec]
- Renamed to dlg_gen_pal. [Andreas Wicenec]
- Win pip upgrade changed command. [awicenec]
- ✅ Ready to clone and code. [awicenec]
- Initial commit. [awicenec]


