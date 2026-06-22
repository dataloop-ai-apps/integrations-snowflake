# Snowflake Integration

This repository provides a service that enables seamless interaction between **Snowflake** and **DDOE** using **user-password authentification**. The integration is designed to streamline data processing, table updates, and data uploads between Snowflake and DDOE datasets.

## Features

- **Secure Authentication** with **user-password authentication** for Snowflake access.
- **SQL Query Execution** on Snowflake directly from DDOE using the integrated service.
- **Dynamic Table Creation and Updates**: Automatically create and update tables based on DDOE dataset information.
- **Seamless Data Upload**: Upload Snowflake query results directly to DDOE datasets.

## Prerequisites

To set up the integration, you'll need the following information:

- **Account**, which you get from url, like ab12345.eu-central-2.aws
- **user**
- **password**
- **Warehouse, Database, Schema and Table Name** in Snowflake with at least the following columns:
  - **`id`**: Auto-generated field.
  - **`prompt`**: The prompt to create in DDOE.
  - **`response`**: Field to store model responses (auto-populated from the RLHF pipeline).

## Pipeline Nodes

- **Import Snowflake**

  - This node retrieves prompts from a selected Snowflake table and adds them to a specified dataset in DDOE, creating prompt items accordingly.

- **Export Snowflake**
  - This node takes the response marked as the best and updates the corresponding Snowflake table row with the response, model name and ID from DDOE.

## Acknowledgments

This project uses the following open-source software:

- [PyMySQL](https://github.com/PyMySQL/PyMySQL): A pure Python MySQL client library. Licensed under the [MIT License](https://opensource.org/licenses/MIT).
