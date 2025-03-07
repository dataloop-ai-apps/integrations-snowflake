import os
import logging
import snowflake.connector
import dtlpy as dl
import pandas as pd

logger = logging.getLogger(name="snowflake-connect")


class SnowflakeBase(dl.BaseServiceRunner):
    """
    A class for running a service that interacts with Snowflake.
    """

    def __init__(self):
        """
        Initializes the ServiceRunner with Snowflake credentials.
        """
        self.logger = logger

    def create_snowflake_connection(self, account: str, user: str, warehouse: str, database: str, schema: str):
        """
        Creates a connection to Snowflake.

        :param account: The Snowflake account.
        :param user: The Snowflake user.
        :param password: The Snowflake password.
        :param warehouse: The Snowflake warehouse.
        :param database: The Snowflake database.
        :param schema: The Snowflake schema.
        :return: The Snowflake connection.
        """
        self.logger.info("Creating Snowflake connection.")
        conn = snowflake.connector.connect(
            user=user,
            password=os.environ.get("SNOWFLAKE_PASSWORD"),
            account=account,
            warehouse=warehouse,
            database=database,
            schema=schema,
            application='Dataloop_ConnectorNode'
        )
        self.logger.info("Successfully created Snowflake connection.")
        return conn

    def table_to_dataloop(
        self, account: str, user: str, warehouse: str, database: str, schema: str, table_name: str, dataset_id: str
    ):
        """
        Fetches data from a Snowflake table and uploads it to a Dataloop dataset.

        :param account: The Snowflake account.
        :param user: The Snowflake user.
        :param warehouse: The Snowflake warehouse.
        :param database: The Snowflake database.
        :param schema: The Snowflake schema.
        :param table_name: The Snowflake table name.
        :param dataset_id: The Dataloop dataset ID.
        :return: The uploaded items or None if an error occurs.
        """

        self.logger.info("Creating table for dataset '%s' and table '%s'.", dataset_id, table_name)

        try:
            dataset = dl.datasets.get(dataset_id=dataset_id)
            self.logger.info("Successfully retrieved dataset with ID '%s'.", dataset_id)
        except dl.exceptions.NotFound as e:
            self.logger.error("Failed to get dataset with ID '%s': %s", dataset_id, e)
            return None

        # Execute query to fetch data
        query = f"SELECT * FROM {table_name}"
        conn = self.create_snowflake_connection(
            account=account, user=user, warehouse=warehouse, database=database, schema=schema
        )
        df = pd.read_sql(query, conn)
        conn.close()

        prompt_items = []
        for i, row in df.iterrows():
            prompt_item = dl.PromptItem(name=str(row.ID))
            prompt_item.add(
                message={"role": "user", "content": [{"mimetype": dl.PromptType.TEXT, "value": row.PROMPT}]}
            )
            prompt_items.append(prompt_item)

        # Upload PromptItems to Dataloop
        items = list(dataset.items.upload(local_path=prompt_items, overwrite=True))
        self.logger.info("Successfully uploaded %d items to dataset '%s'.", len(items), dataset_id)
        return items

    def update_table(
        self, item: dl.Item, account: str, user: str, warehouse: str, database: str, schema: str, table_name: str
    ):
        """
        Updates a Snowflake table with the best response from a Dataloop item.

        :param item: The Dataloop item.
        :param account: The Snowflake account.
        :param user: The Snowflake user.
        :param warehouse: The Snowflake warehouse.
        :param database: The Snowflake database.
        :param schema: The Snowflake schema.
        :param table_name: The Snowflake table name.
        :return: The updated item or None if an error occurs.
        """

        self.logger.info("Updating table '%s' for item with ID '%s'.", table_name, item.id)

        prompt_item = dl.PromptItem.from_item(item)
        first_prompt_key = prompt_item.prompts[0].key

        # Find the best response based on annotation attributes
        best_response = None

        for resp in item.annotations.list():
            try:
                is_best = resp.attributes.get("isBest", False)
            except AttributeError:
                is_best = False
            if is_best and resp.metadata["system"].get("promptId") == first_prompt_key:
                best_response = resp.coordinates
                break

        if best_response is None:
            self.logger.error("No best response found for item ID: %s", item.id)
            return None

        conn = self.create_snowflake_connection(
            account=account, user=user, warehouse=warehouse, database=database, schema=schema
        )
        cursor = conn.cursor()
        update_query = f"""
                        UPDATE {table_name}
                        SET RESPONSE = %s
                        WHERE ID = %s
                        """
        self.logger.info(
            "Updating table '%s' for item with ID '%s' with response: %s", table_name, item.id, best_response
        )
        cursor.execute(update_query, (best_response, int(prompt_item.name[:-5])))
        conn.commit()  # Commit the changes
        cursor.close()
        conn.close()
        self.logger.info("Successfully updated table '%s' for item with ID '%s'.", table_name, item.id)
        return item
