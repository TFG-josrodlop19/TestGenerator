# AutoFuzz: Tool for Automated Vulnerability Detection and Fuzz Test Generation

## What is AutoFuzz?
Autofuzz is a tool designed to automate the process of detecting and validating vulnerabilities in the software supply chain. It identifies known vulnerabilities in a project's dependencies and generates fuzzing tests to validate whether these vulnerabilities are exploitable in the specific context of the project. The entire process is automated, from vulnerability detection to test generation and execution.

## Features
- **Automated Vulnerability Detection**: Scans project dependencies to identify known vulnerabilities using public vulnerability databases. This process is delegated to VEXGen, a SCA tool that generates VEX documents for the identified vulnerabilities. 
- **Fuzz Test Generation**: Automatically generates fuzzing tests based on the identified vulnerabilities and the project's codebase. These tests are designed to validate whether the vulnerabilities can be exploited in the specific context of the project.
- **Automated Test Execution**: Runs the generated fuzzing tests and reports the results, indicating whether any vulnerabilities were successfully exploited. This step is handled by OSS-Fuzz platform, which provides a robust environment for fuzz testing developed by Google.
- **Project Support**: Currently supports projects written in Java and build with Maven. Another prerequisite is that the project must be public and hosted on GitHub and contains a valid pom.xml and sbom.json file.

- **OS Support**: The tool is designed to run on Ubuntu (minimum version 20.04). It may work on other Debian-based distributions, but this is not guaranteed as it has only been tested on Ubuntu.


## Installation
To install AutoFuzz, follow these steps:
1. Clone the repository:
   ```bash
   git clone https://github.com/TFG-josrodlop19/TestGenerator.git
   ```
2. Navigate to the project directory:
   ```bash
   cd TestGenerator
   ```
3. Copy template.env to .env and modify it if necessary (it works with default values):
   ```bash
   cp template.env .env
   ```
4. Execute the installation script with sudo privileges:
   ```bash
   sudo scripts/install.sh
   ```

## How to Use
Autofuzz is a tool that runs from the command line. To use it, you just need to type the following command in the terminal:
```bash
autofuzz <command>
```
Replace `<command>` with the desired command to execute. For example, to execute the complete pipeline, you would use:
```bash
autofuzz run <owner of the repository> <repository name> <pom file path>
```

For extra details about the available commands and their usage, use the following command:
```bash
autofuzz --help
```

## Contributions
This project does not accept external contributions as it is an academic project developed for a final degree project.