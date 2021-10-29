# Introduction
The _capa-tool-launcher_ is a research tool to launch the [Mandiant capa tool](https://www.mandiant.com/resources/capa-automatically-identify-malware-capabilities) in order to analyse multiple repositories and postprocess the obtained results. As further detailed in this guide, the tool is currently implemented as a python script (`capatoolauncher.py`) that relies on a module (`capapostprocesslib`) containing classes developed for postprocessing-related tasks. Additional information on the most recent releases of capa tool can be found in these blog posts:

* [capa 2.0: Better, Stronger, Faster] (https://www.mandiant.com/resources/capa-2-better-stronger-faster)
* [ELFant in the Room – capa v3] (https://www.fireeye.com/blog/threat-research/2021/09/elfant-in-the-room-capa-v3.html)

# Main Features
The _capa-tool-launcher_ relies on the capa standalone binary. While Mandiant provides the tool as a Python module as well, using the standalone binary is advantageous as it does not require any installation. In essence, the script `capatoolauncher.py`, which includes a command-line interface implemented with the Python Standard Library module `argparse`, allows executing the relevant binary by using the **Linux** shell. It should be observed that:

* The tool was implemented and tested under Linux. Ubuntu Linux 18.04 LTS was used both for development and testing.
* The Python version the tool is currently compatible with is **Python 3.6.9**.
* The capa version **v3.0.2** was used during the latest tests conducted with the _capa-tool-launcher_.

Since the Linux shell is used to launch the capa binary, the tool relies on the _exit codes_ for an high-level classification of the execution. This means that the execution of test is categorized as _Successful_ if the returned exit code is zero, though the author has observed that this does not necessarily mean that capa has identified any capabilities. When an exit code different from zero is obtained, the tool processes stderr and extracts the available information, which is then logged in the generated summary report. When the process of extracting this information fails, the test execution is classified as _Other_.

In addition, tests performed during the development of the capa tool show that in some cases the execution time is unexpectedly long, and, when this happens, the OS automatically kills the execution, which, therefore, does not yield any results. As tool was primarily conceived to support researchers and analysts who have to process large file repositories, the capa binary is launched with the Linux command `timeout` to avoid slowing down the analysis unnecessarily.

Finally, the tool includes a command-line interface, which can be displayed with the usual `-h` option (i.e., `python3 capatoolauncher.py -h`), and support different execution modes, which are illustrated in a dedicated section included in this guide.

# Known Issues and Limitations
The following known issues and limitations should be considered prior to starting using the tool:

* **Security**. To facilitate the redirection of the capa results to a JSON file, which is possible by calling the standalone binary with the `-j` option (automatically done by the _capa-tool-launcher_), the option `shell=True` was used in the interface towards the Linux shell (i.e., as input argument to the `subprocess` module function used to access the shell). This means that the tool should **not** be used with an unchecked configuration file, as execution of arbitrary code is possible. Details about are the tool configuration file are provided in the description of the analisys execution mode.
* **Python version**. More recent Python versions than the used to develop and test the tool include an updated version of the Standard Library module `subprocess`. Consequently, it is **not** at all guaranteed that the current implementation of the _capa-tool-launcher_ works with these version of the language.
* **Timeout duration**. The duration of the above-mentioned timeout is currently set to 5 minutes. This parameter is **not** currently included in the configuration file. This is an improvement to be considered for future releases to allow users to further tailor their analysis set-up.   

# Execution Modes
The purpose of this section is to illustrate the tool execution modes. The corresponding command-line options along with implementation strategies and limitations are described.

## Remove Results Mode
TBC



## Analysis Mode
Explain the -j and -f option (-f elf)



## Postprocessing Mode
TBC


## Complete Execution Mode
TBC

## Merge Mode
TBC
